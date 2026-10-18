# %% [markdown]
# # Financial Services Executive Risk Dashboard — AIDP
#
# Reads `finance.gold.transaction_analytics_gold` and `finance.gold.fraud_detection_model_gold`
# created by `financial_services_medallion_architecture_demo.ipynb`. Run that notebook first.
# This notebook reads Gold only, creates no source data, and does not change medallion tables.
#
# **Decision:** Where should fraud-operations leaders focus analyst investigation this month?
# **Scope:** synthetic account activity, transaction-risk flags, gross exposure, concentration and evidence.
# Amounts are **assumed INR**, as requested; the source has no currency column. No FX conversion is applied.
# These are risk-screening signals, not confirmed fraud, realized loss, account balances, revenue or EBITDA.
# Source locations remain the original US/Online/ATM labels; currency labeling does not localize the dataset.
#
# The source generator uses random data over 2024 and no fixed seed. Your totals vary by run.
# The default is the latest **observed** month, with no claim of calendar completeness or real-time freshness.

# %% [markdown]
# ## 1. Setup and reporting scope
# Uses the existing AIDP Spark session, Matplotlib and IPython. No Pandas/Arrow conversion or LLM is required.
# Account filters apply to every view, chart, denominator and brief. Monthly active accounts are not additive over months.

# %%
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from matplotlib.dates import DateFormatter
from IPython.display import HTML, Markdown, display

CATALOG = "finance"
REPORT_MONTH = None                 # None = latest observed; or '2024-06'.
ACCOUNT_IDS = []                     # [] = all; e.g. ['ACC00000001'].
TREND_MONTHS = 12
TOP_N = 10
ENABLE_ENTERPRISE_LLM = False        # Optional enterprise_llm(prompt) callable; never required.
plt.rcParams.update({"figure.figsize": (11, 4.5), "font.size": 11,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.alpha": 0.2})
COLORS = {"activity": "#245b73", "flag": "#ad6424", "neutral": "#606c72"}
display(HTML("<style>th,td{padding:9px 12px;text-align:left;border-bottom:1px solid #ddd}th{background:#eef3f4}table{font-size:13px}</style>"))

# %% [core]

# %% [markdown]
# ## 2. Validate the actual Gold contract
# The supplied medallion notebook overwrites the DDL tables with DataFrames that omit several declared timestamp
# columns. Validation therefore uses columns actually written. `is_fraud = (risk_score > 60)` is a synthetic
# rule label; the saved Gold table contains ML inputs, not predictions or fraud probabilities.

# %%
transactions_all, monthly_all = read_gold(spark, CATALOG)
source_fingerprint_at_start = content_fingerprint(transactions_all, monthly_all)
source_periods = [r["month_year"] for r in transactions_all.select("month_year").distinct().orderBy("month_year").limit(241).collect()]
if len(source_periods) > 240:
    raise ValueError("More than 240 observed months; choose a bounded source window before collecting periods")
if not isinstance(TREND_MONTHS, int) or not 1 <= TREND_MONTHS <= 24:
    raise ValueError("TREND_MONTHS must be between 1 and 24")
if not isinstance(TOP_N, int) or not 1 <= TOP_N <= 50:
    raise ValueError("TOP_N must be between 1 and 50")
if REPORT_MONTH is not None and not re.fullmatch(r"[0-9]{4}-(0[1-9]|1[0-2])", REPORT_MONTH):
    raise ValueError("REPORT_MONTH must be YYYY-MM")
if REPORT_MONTH is not None and REPORT_MONTH not in source_periods:
    raise ValueError(f"Requested month {REPORT_MONTH} unavailable. Observed: {source_periods}")
report_month = REPORT_MONTH or source_periods[-1]
if not isinstance(ACCOUNT_IDS, list) or any(not isinstance(a, str) or not re.fullmatch(r"ACC[0-9]{8}", a) for a in ACCOUNT_IDS):
    raise ValueError("ACCOUNT_IDS must be a list of ACC followed by eight digits")
if ACCOUNT_IDS:
    found = {r["account_id"] for r in transactions_all.filter(F.col("account_id").isin(ACCOUNT_IDS)).select("account_id").distinct().collect()}
    if set(ACCOUNT_IDS) - found:
        raise ValueError(f"Unknown account IDs: {sorted(set(ACCOUNT_IDS) - found)}")
scope_filter = F.col("account_id").isin(ACCOUNT_IDS) if ACCOUNT_IDS else F.lit(True)
window_start = F.add_months(F.to_date(F.lit(report_month + "-01")), -(TREND_MONTHS - 1))
tx = transactions_all.filter(scope_filter & (F.to_date(F.concat(F.col("month_year"), F.lit("-01"))) >= window_start) & (F.col("month_year") <= report_month)).cache()
gold_monthly = monthly_all.filter(scope_filter & (F.to_date(F.concat(F.col("month_year"), F.lit("-01"))) >= window_start) & (F.col("month_year") <= report_month))
snapshot = tx.filter(F.col("month_year") == report_month)
if not snapshot.take(1):
    raise ValueError("Selected accounts have no activity in the requested month; choose another month or account")
quality = reconciliation_checks(tx, gold_monthly)
accounts = account_metrics(tx).cache()
portfolio = portfolio_metrics(accounts).cache()
current = portfolio.filter(F.col("month_year") == report_month).first().asDict()
scope_label = "All accounts" if not ACCOUNT_IDS else ", ".join(ACCOUNT_IDS)
print(f"Period: {report_month} | Scope: {scope_label} | INR assumption, no FX conversion")
print(f"Observed source periods: {source_periods[0]} to {source_periods[-1]} | fingerprint: {source_fingerprint_at_start}")

# %% [markdown]
# ## 3. Executive snapshot
# Gross activity = `SUM(ABS(amount))`; net activity = `SUM(amount)`. Positive and negative amounts follow the
# source's sign convention. Transfers have no counterparty or direction field. Flagged gross is the absolute
# amount of transactions with score **strictly greater than 60**. It is an investigation exposure proxy.

# %%
cards = [
    ("Transactions", f"{current['transaction_count']:,}", "Selected month and account scope"),
    ("Active accounts", f"{current['active_accounts']:,}", "Distinct accounts in selected month"),
    ("Gross activity · INR", inr(current["gross_amount_inr"]), "Absolute transaction amounts"),
    ("Net activity · INR", inr(current["net_amount_inr"]), "Signed sum; not an account balance"),
    ("Rule-flagged activity", f"{current['flagged_count']:,} · {current['flagged_rate_pct']:.1f}%", "risk_score > 60; not confirmed fraud"),
    ("Flagged gross · INR", inr(current["flagged_gross_inr"]), "Exposure proxy; not loss or savings"),
]
display(HTML("<div style='display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px'>" +
    "".join(f"<div style='padding:16px;border:1px solid #ccd5d8;border-top:4px solid #245b73;border-radius:6px'><div>{escape(label)}</div><strong style='font-size:24px'>{escape(value)}</strong><div style='font-size:12px;margin-top:8px'>{escape(note)}</div></div>" for label, value, note in cards) + "</div>"))
display(Markdown(f"**Priority queue:** {current['p1_accounts']:,} P1 accounts under fictional policy `{RULE_VERSION}`. "
                 f"Average rule score: {current['avg_risk_score']:.2f}/100; this score is not a probability."))

# %% [markdown]
# ## 4. Activity and risk trends
# An absent calendar month is shown as a gap, never silently treated as zero or skipped in a month-over-month comparison.
# Prior-month comparison uses the immediately preceding calendar month and the same account scope.

# %%
trend_rows = rows(portfolio.orderBy("month_year"), 24)
calendar = spark.range(TREND_MONTHS).select(F.date_format(F.add_months(F.to_date(F.lit(report_month + "-01")), -F.col("id").cast("int")), "yyyy-MM").alias("month_year"))
trend_rows = rows(calendar.join(portfolio, "month_year", "left").orderBy("month_year"), 24)
dates = [datetime.strptime(r["month_year"], "%Y-%m") for r in trend_rows]
def values(key, divisor=1):
    return [float(r[key]) / divisor if r.get(key) is not None else float("nan") for r in trend_rows]
fig, axes = plt.subplots(2, 1, figsize=(11, 7), sharex=True)
axes[0].plot(dates, values("transaction_count"), marker="o", color=COLORS["activity"], label="All transactions")
axes[0].plot(dates, values("flagged_count"), marker="s", linestyle="--", color=COLORS["flag"], label="Rule-flagged transactions")
axes[0].set(ylabel="Transactions", title=f"Monthly transaction activity · {scope_label}"); axes[0].legend()
axes[1].plot(dates, values("flagged_rate_pct"), marker="s", color=COLORS["flag"])
axes[1].set(ylabel="Flagged transactions (%)", xlabel="Observed calendar month", title="Rule-flagged rate · same population")
axes[1].set_ylim(0, 100)
tick_dates = [dates[i] for i in sorted(set(range(0, len(dates), max(1, len(dates)//5))) | {len(dates)-1})]
axes[1].set_xticks(tick_dates); axes[1].xaxis.set_major_formatter(DateFormatter("%b %Y"))
fig.autofmt_xdate(rotation=0); fig.tight_layout(); plt.show()
previous_month = spark.range(1).select(F.date_format(F.add_months(F.to_date(F.lit(report_month + "-01")), -1), "yyyy-MM").alias("m")).first()["m"]
previous = portfolio.filter(F.col("month_year") == previous_month).first()
if previous is None:
    display(Markdown(f"Calendar comparison unavailable for {previous_month} in this trend window and scope."))
else:
    delta_pp = current["flagged_rate_pct"] - previous["flagged_rate_pct"]
    display(Markdown(f"{report_month}: flagged rate {current['flagged_rate_pct']:.2f}% versus {previous['flagged_rate_pct']:.2f}% in {previous_month}; change **{delta_pp:+.2f} percentage points**."))

# %%
fig, ax = plt.subplots()
ax.plot(dates, values("gross_amount_inr", 100000), marker="o", color=COLORS["activity"], label="Gross activity")
ax.plot(dates, values("flagged_gross_inr", 100000), marker="s", linestyle="--", color=COLORS["flag"], label="Flagged gross")
ax.set(title=f"Monthly gross activity and flagged exposure · {scope_label}", ylabel="INR lakh (₹100,000)", xlabel="Calendar month")
ax.set_ylim(bottom=0); ax.legend()
ax.set_xticks(tick_dates); ax.xaxis.set_major_formatter(DateFormatter("%b %Y"))
fig.autofmt_xdate(rotation=0); fig.tight_layout(); plt.show()
display(Markdown("These measures use transaction magnitudes. They do not measure deposits held, revenue, realized loss or avoided loss."))

# %% [markdown]
# ## 5. Investigation queue and concentration
# P1: flagged gross ≥ ₹10,000 per account-month **or** at least one transaction with score ≥ 85 and
# absolute amount ≥ ₹5,000. P2: other accounts with score > 60 activity. P3: no flagged activity.
# These fictional demo thresholds prioritize analyst review; they are not regulatory standards or model outputs.

# %%
account_snapshot = accounts.filter(F.col("month_year") == report_month)
priority_rows = rows(account_snapshot.filter(F.col("flagged_count") > 0).orderBy(F.desc("flagged_gross_inr"), F.desc("flagged_count"), "account_id"), TOP_N)
formatted = [{**r, "flagged_gross_display": inr(r["flagged_gross_inr"]), "gross_display": inr(r["gross_amount_inr"]), "rate_display": f"{r['flagged_rate_pct']:.1f}%"} for r in priority_rows]
display(HTML(table_html(formatted, [("account_id","Synthetic account"),("priority","Demo priority"),("transaction_count","Transactions"),("flagged_count","Rule flags"),("flagged_gross_display","Flagged gross INR"),("rate_display","Flag rate"),("high_value_flagged_count","Flags ≥ ₹5,000") ])))
top_exposure = sum(float(r["flagged_gross_inr"]) for r in priority_rows)
concentration_pct = 100 * top_exposure / current["flagged_gross_inr"] if current["flagged_gross_inr"] else None
display(Markdown(f"Showing {len(priority_rows)} accounts ranked by flagged gross. " +
    (f"They represent **{concentration_pct:.1f}%** of this month's flagged gross in the selected scope." if concentration_pct is not None else "No rule-flagged gross exposure in this scope.")))
if priority_rows:
    data = list(reversed(priority_rows))
    fig, ax = plt.subplots(figsize=(11, max(4, len(data)*0.35)))
    ax.barh([r["account_id"] for r in data], [r["flagged_gross_inr"] for r in data], color=COLORS["flag"])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"₹{value:,.0f}"))
    ax.set(title=f"Top {len(data)} accounts by flagged gross · {report_month}", xlabel="Flagged gross · INR")
    fig.tight_layout(); plt.show()

# %% [markdown]
# ## 6. Transaction type, location and score distribution
# Transaction type is not a channel taxonomy. Locations are source labels, not customer residence or geolocation.
# No counterparty, transfer destination, customer KYC, sanctions result or device data exists in these sources.

# %%
mix_tables = {}
for dimension, title in [("transaction_type", "Transaction type"), ("location", "Location label")]:
    mix = snapshot.groupBy(dimension).agg(F.count("*").alias("transactions"), F.sum("rule_flag").alias("flags"),
        F.sum(F.when(F.col("rule_flag") == 1, F.col("gross_amount_inr")).otherwise(0)).alias("flagged_gross_inr"))
    data = rows(mix.orderBy(F.desc("flagged_gross_inr"), dimension), 30)
    mix_tables[dimension] = data
    fig, ax = plt.subplots()
    ax.barh([str(r[dimension]) for r in data][::-1], [r["flagged_gross_inr"] for r in data][::-1], color=COLORS["activity"])
    ax.xaxis.set_major_formatter(FuncFormatter(lambda value, pos: f"₹{value/100000:,.2f}L"))
    ax.set(title=f"Flagged gross by {title.lower()} · {report_month}", xlabel="Flagged gross · INR lakh")
    fig.tight_layout(); plt.show()

# %%
band = (F.when(F.col("risk_score") <= 20, "00–20").when(F.col("risk_score") <= 40, "21–40")
        .when(F.col("risk_score") <= 60, "41–60").when(F.col("risk_score") <= 80, "61–80").otherwise("81–100"))
risk_rows = rows(snapshot.withColumn("score_band", band).groupBy("score_band").count().orderBy("score_band"), 5)
fig, ax = plt.subplots()
ax.bar([r["score_band"] for r in risk_rows], [r["count"] for r in risk_rows], color=COLORS["activity"])
ax.set(title=f"Rule-score distribution · {report_month}", xlabel="Source risk score (0–100)", ylabel="Transactions")
fig.tight_layout(); plt.show()
display(Markdown("The generator assigns risk scores randomly. Any apparent pattern is synthetic; this chart does not validate a detection model."))

# %% [markdown]
# ## 7. Gold-grounded executive brief
# Deterministic arithmetic generates the default brief. Optional LLM wording receives only aggregated evidence.
# No customer contact, account freeze, case creation, payment intervention or filing is performed.

# %%
leader = priority_rows[0] if priority_rows else None
brief = (f"## Investigation review · {report_month}\n\n"
         f"Scope: {scope_label}. Synthetic amounts assumed INR; no currency conversion.\n\n"
         f"- {current['transaction_count']:,} transactions across {current['active_accounts']:,} active accounts; gross activity {inr(current['gross_amount_inr'])}.\n"
         f"- {current['flagged_count']:,} rule flags ({current['flagged_rate_pct']:.2f}%) represent {inr(current['flagged_gross_inr'])} flagged gross. This is not confirmed fraud or loss.\n"
         f"- {current['p1_accounts']:,} account-months meet fictional P1 review criteria under {RULE_VERSION}.\n")
if leader:
    brief += f"- Review {leader['account_id']} first by exposure: {inr(leader['flagged_gross_inr'])}, {leader['flagged_count']} rule flags; queue priority {leader['priority']}.\n"
brief += ("\n**Next step:** Retrieve the applicable synthetic policy and transaction evidence through the Agent Flow; draft an analyst investigation packet. Human review is required before any action.\n\n"
          "**Evidence:** the two finance Gold tables, scoped as above. Neither model predictions nor confirmed fraud labels are persisted in these tables. AUC from the training notebook is not consumed or certified here.")
display(Markdown(brief))
if ENABLE_ENTERPRISE_LLM:
    callback = globals().get("enterprise_llm")
    if not callable(callback):
        raise RuntimeError("ENABLE_ENTERPRISE_LLM=True requires an authorized enterprise_llm(prompt) callable")
    evidence = json.dumps({"period": report_month, "scope": scope_label, "metrics": current, "source_fingerprint": source_fingerprint_at_start}, default=str)
    response = callback("Rewrite the supplied synthetic aggregate evidence into an INR investigation brief. Preserve numbers, scope, caveats and sources exactly. Do not infer confirmed fraud, loss, causal drivers or probabilities. Evidence: " + evidence)
    display(Markdown("### Optional LLM draft — requires analyst verification\n" + str(response)))

# %% [markdown]
# ## 8. Reconciliation and handoff
# Checks reconcile both Gold tables at account-month grain, validate category maps, verify scope totals and
# confirm the source content fingerprint did not change during the run. This fingerprint is a multiset checksum,
# not a Delta commit/version or an immutable audit record. Rerun after any source refresh.

# %%
assert abs(current["positive_amount_inr"] - current["negative_magnitude_inr"] - current["net_amount_inr"]) < 0.02
assert 0 <= current["flagged_count"] <= current["transaction_count"]
assert current["flagged_gross_inr"] <= current["gross_amount_inr"] + 0.02
assert abs(sum(float(r["flagged_gross_inr"]) for r in mix_tables["transaction_type"]) - current["flagged_gross_inr"]) < 0.02
source_fingerprint_at_end = content_fingerprint(*read_gold(spark, CATALOG))
assert source_fingerprint_at_start == source_fingerprint_at_end, "Source changed during dashboard run; rerun"
quality.update({"signed_amount_identity": "PASS", "risk_bounds": "PASS", "type_mix_totals": "PASS", "stable_source_content": "PASS"})
display(HTML(table_html([{"check": key, "status": value} for key, value in quality.items()], [("check", "Quality check"), ("status", "Result")])))
print("Dashboard checks passed for this run. Next: financial_services_multi_agent_demo_setup_aidp.ipynb")
tx.unpersist(); accounts.unpersist(); portfolio.unpersist()

# %% [markdown]
# **Source adaptation:** replaces manufacturing P&L with transaction activity; plants/products with account risk;
# supplier/inventory panels with type/location exposure; model-probability panels with an honest rule-score view.
# It preserves executive cards, trends, ranked actions, deterministic briefing, bounded `.collect()` and reconciliation.
# Open `docs/agent_flow_build_guide.html` for the SQL + RAG investigation workflow and manual AIDP acceptance steps.
