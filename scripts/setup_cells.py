# %% [markdown]
# # Financial Services Multi-Agent Demo Setup — AIDP
#
# **Use case:** high-value suspicious-transaction investigation, grounded in finance medallion Gold and
# a self-contained synthetic policy corpus. Produces an analyst briefing packet with SQL evidence and document citations.
# All monetary amounts are assumed USD; no FX conversion is applied. This is not a confirmed-fraud, AML,
# regulatory-reporting or automated account-action system.
#
# Run `financial_services_medallion_architecture_demo.ipynb` first. This setup reads its two existing Gold tables
# and writes **only** to the dedicated `finance.agent_demo_fs` schema. It does not retrain a model or change Bronze,
# Silver or Gold. Physical Delta tables support catalog discovery by SQL tools. Rerunning refreshes this dedicated
# demo schema's named tables; it never drops a schema.
#
# This notebook prepares data, registries and documents. Create the Agent Flow and ingest the Knowledge Base
# manually using `docs/agent_flow_build_guide.html`. No `.aflow` import format is fabricated.

# %% [markdown]
# ## 1. Setup
# Both notebooks are self-contained. SQL tools, prompts, acceptance cases and corpus text are embedded below;
# the external package copies are for convenient review. No additional Python installation is needed in AIDP.

# %%
from pathlib import Path
from IPython.display import HTML, display

CATALOG = "finance"
AGENT_SCHEMA_NAME = "agent_demo_fs"
AGENT_SCHEMA = f"{CATALOG}.{AGENT_SCHEMA_NAME}"
WRITE_RAG_DOCUMENTS = False
RAG_OUTPUT_DIRECTORY = None      # Set an existing notebook-accessible managed/external volume folder.
print(f"Read source: {CATALOG}.gold; publish demo-only objects: {AGENT_SCHEMA}")

# %% [core]

# %% [markdown]
# ## 2. Validate and reconcile source data
# Reconciliation covers all source account-months before creating an agent-facing snapshot. No trained-model
# probability is published. The source's `is_fraud` field is a score-threshold label, not an investigator outcome.

# %%
transactions, gold_monthly = read_gold(spark, CATALOG)
source_fingerprint = content_fingerprint(transactions, gold_monthly)
source_checks = reconciliation_checks(transactions, gold_monthly)
account_monthly = account_metrics(transactions).cache()
portfolio_monthly = portfolio_metrics(account_monthly).cache()
latest_row = portfolio_monthly.orderBy(F.desc("period_key")).first().asDict()
latest_period_key = int(latest_row["period_key"])
period_coverage = portfolio_monthly.agg(F.min("period_key").alias("min_period_key"), F.max("period_key").alias("max_period_key"), F.count("*").alias("observed_months")).first().asDict()
snapshot_id = hashlib.sha256((source_fingerprint + RULE_VERSION + CURRENCY_ASSUMPTION).encode()).hexdigest()[:24]
prepared_at_utc = datetime.utcnow().isoformat(timespec="seconds") + "Z"
spark_session_timezone = spark.conf.get("spark.sql.session.timeZone")
print("Latest observed period:", latest_period_key, "| Snapshot:", snapshot_id, "| Rule:", RULE_VERSION)

# %% [markdown]
# ## 3. Materialize a governed semantic surface
# The source has no transaction ID. Evidence rows group identical source records and expose
# `duplicate_multiplicity` plus a content fingerprint. The fingerprint is not a unique transaction identifier.
# No apparent duplicate is silently removed from financial totals.
#
# `snapshot_metadata_sql` is marked PREPARING before table refresh and READY only after checks pass.
# Tool queries select READY data with matching snapshot IDs. Tables are refreshed sequentially, not in one transaction;
# agents must compare snapshot IDs across tool responses and stop if they differ. Rerun after every medallion refresh.

# %%
if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", AGENT_SCHEMA_NAME):
    raise ValueError("AGENT_SCHEMA_NAME must be a simple schema identifier")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {AGENT_SCHEMA}")

def publish(df, short_name):
    if not re.fullmatch(r"[a-z_]+", short_name):
        raise ValueError("Invalid demo object name")
    (df.write.format("delta").mode("overwrite").option("overwriteSchema", "true")
       .saveAsTable(f"{AGENT_SCHEMA}.{short_name}"))

def enrich(df, source_tables, grain):
    return (df.withColumn("snapshot_id", F.lit(snapshot_id))
            .withColumn("prepared_at_utc", F.lit(prepared_at_utc))
            .withColumn("source_tables", F.lit(source_tables))
            .withColumn("grain", F.lit(grain))
            .withColumn("currency_assumption", F.lit(CURRENCY_ASSUMPTION))
            .withColumn("rule_version", F.lit(RULE_VERSION))
            .withColumn("risk_threshold_exclusive", F.lit(RISK_THRESHOLD))
            .withColumn("high_value_usd", F.lit(HIGH_VALUE_USD))
            .withColumn("p1_account_exposure_usd", F.lit(P1_ACCOUNT_EXPOSURE_USD))
            .withColumn("very_high_score_inclusive", F.lit(VERY_HIGH_SCORE)))

def metadata_frame(status):
    record = (snapshot_id, source_fingerprint, prepared_at_utc, status,
              int(period_coverage["min_period_key"]), int(period_coverage["max_period_key"]),
              int(period_coverage["observed_months"]), spark_session_timezone, RULE_VERSION, CURRENCY_ASSUMPTION)
    return spark.createDataFrame([record], "snapshot_id string, source_fingerprint string, prepared_at_utc string, status string, min_period_key int, max_period_key int, observed_months int, spark_session_timezone string, rule_version string, currency_assumption string")

publish(metadata_frame("PREPARING"), "snapshot_metadata_sql")
gold_source = f"{CATALOG}.gold.fraud_detection_model_gold"
publish(enrich(portfolio_monthly, gold_source, "month"), "portfolio_monthly_sql")
publish(enrich(account_monthly, gold_source, "account x month"), "account_risk_monthly_sql")

evidence_columns = ["account_id", "month_year", "period_key", "transaction_date", "transaction_type", "amount", "merchant_category", "location", "risk_score", "is_fraud"]
transaction_evidence = (transactions.groupBy(*evidence_columns).agg(F.count("*").alias("duplicate_multiplicity"))
    .withColumn("source_row_fingerprint", F.sha2(F.to_json(F.struct(*evidence_columns)), 256))
    .withColumn("gross_amount_usd", F.abs("amount").cast("double"))
    .withColumnRenamed("is_fraud", "synthetic_rule_label"))
publish(enrich(transaction_evidence, gold_source, "source row content group; retain multiplicity"), "transaction_evidence_sql")

mix_frames = []
for code, dimension in [(1, "transaction_type"), (2, "location")]:
    df = transactions.groupBy("month_year", "period_key", dimension).agg(
        F.count("*").alias("transaction_count"), F.sum("rule_flag").alias("flagged_count"),
        F.sum("gross_amount_usd").alias("gross_amount_usd"),
        F.sum(F.when(F.col("rule_flag") == 1, F.col("gross_amount_usd")).otherwise(0)).alias("flagged_gross_usd"))
    mix_frames.append(df.withColumnRenamed(dimension, "dimension_value").withColumn("dimension_code", F.lit(code)))
exposure_mix = mix_frames[0].unionByName(mix_frames[1])
publish(enrich(exposure_mix, gold_source, "month x dimension code x dimension value; never sum across dimension codes"), "exposure_mix_monthly_sql")
print("Four physical Delta data tables published; snapshot remains PREPARING pending validation.")

# %% [markdown]
# ## 4. Embedded SQL-tool registry
# Predefined queries use **Spark SQL**, with catalog `finance`, schema `agent_demo_fs`, an active Spark cluster,
# and a separate active AI Compute for the Agent Flow. Runtime placeholders are `{{name}}`.
# Query parameters are numeric period/account selectors, not arbitrary SQL or string fragments.
# Configure numeric types in the UI and a read-only data principal. These templates are not a database
# prepared-statement API; prompt instructions and parameter descriptions are not authorization controls.

# %% [config]

# %%
# Remap only identifiers when CATALOG or AGENT_SCHEMA_NAME is changed at the top.
for tool in SQL_TOOLS:
    tool["query"] = tool["query"].replace("finance.agent_demo_fs.", AGENT_SCHEMA + ".")
    tool["configuration"]["catalogKey"] = CATALOG
    tool["configuration"]["schemaKey"] = AGENT_SCHEMA_NAME
    tool["configuration"]["query"] = tool["query"]

def publish_registry(items, table_name, key):
    df = spark.createDataFrame([(item[key], json.dumps(item, sort_keys=True, ensure_ascii=False)) for item in items],
                               f"{key} string, configuration_json string")
    publish(df, table_name)

publish_registry(SQL_TOOLS, "sql_tool_registry", "tool_name")
display(HTML(table_html([{ "name": t["tool_name"], "agent": t["executor_agent"], "max_rows": t["max_rows"]} for t in SQL_TOOLS],
                        [("name", "SQL tool"), ("agent", "Executor"), ("max_rows", "Row cap")])))

# %% [markdown]
# ## 5. Synthetic RAG corpus and lineage
# TXT documents contain document ID, version, effective date, section and fictional-policy notice in their text
# so citations survive chunking. Document metadata is not assumed to become an automatic RAG filter.
# No document asserts a numeric outcome for a randomly generated account. Account-specific quantities come from SQL.

# %%
manifest = []
for document in RAG_DOCUMENTS:
    content_bytes = document["content"].encode("utf-8")
    manifest.append({"document_id": document["document_id"], "filename": document["filename"],
                     "version": document["version"], "effective_from": document["effective_from"],
                     "sha256": hashlib.sha256(content_bytes).hexdigest(), "bytes": len(content_bytes)})
publish_registry(manifest, "rag_document_manifest", "document_id")
if WRITE_RAG_DOCUMENTS:
    if not RAG_OUTPUT_DIRECTORY:
        raise ValueError("Set a notebook-accessible managed/external volume directory before writing corpus files")
    output_dir = Path(RAG_OUTPUT_DIRECTORY)
    if not output_dir.is_dir():
        raise ValueError("RAG_OUTPUT_DIRECTORY must already exist and map to an authorized volume folder")
    for document in RAG_DOCUMENTS:
        (output_dir / document["filename"]).write_text(document["content"], encoding="utf-8")
    print(f"Wrote {len(RAG_DOCUMENTS)} synthetic TXT documents to {output_dir}; manually ingest the Knowledge Base")
else:
    print(f"{len(RAG_DOCUMENTS)} documents embedded. Upload the supplied rag_corpus folder or enable volume writing.")
display(HTML(table_html(manifest, [("document_id", "Document"), ("filename", "File"), ("version", "Version"), ("bytes", "Bytes")])))

# %% [markdown]
# ## 6. Prompts and demo acceptance catalog
# The supervisor delegates SQL and RAG retrieval, then passes the returned evidence explicitly to a stateless
# briefing executor. Instructions require evidence checks and abstention but are not a deterministic enforcement
# mechanism. Guardrails add PII/content/prompt-injection screening; they do not grant approvals or row permissions.

# %%
publish_registry(PROMPTS, "prompt_registry", "name")
publish_registry(ACCEPTANCE_CASES, "demo_acceptance_catalog", "test_id")
for item in PROMPTS:
    print("\n" + item["name"] + "\n" + item["instructions"])

# %% [markdown]
# ## 7. Validate semantic quantities, then publish READY
# These checks exercise Spark and data contracts. They do not claim to test LLM routing, hosted retrieval,
# catalog grants, catalog discovery, Delta behavior or deployment. Run the tool Test and Playground cases next.

# %%
published_portfolio = spark.table(f"{AGENT_SCHEMA}.portfolio_monthly_sql")
published_accounts = spark.table(f"{AGENT_SCHEMA}.account_risk_monthly_sql")
published_evidence = spark.table(f"{AGENT_SCHEMA}.transaction_evidence_sql")
assert published_portfolio.select("month_year").distinct().count() == published_portfolio.count()
assert published_accounts.count() == published_accounts.select("account_id", "month_year").distinct().count()
assert published_evidence.agg(F.sum("duplicate_multiplicity")).first()[0] == transactions.count()
evidence_totals = published_evidence.agg(F.sum(F.col("gross_amount_usd") * F.col("duplicate_multiplicity")).alias("gross")).first()["gross"]
assert abs(float(evidence_totals) - float(portfolio_monthly.agg(F.sum("gross_amount_usd")).first()[0])) < 0.02
for name in ["portfolio_monthly_sql", "account_risk_monthly_sql", "transaction_evidence_sql", "exposure_mix_monthly_sql"]:
    assert {r["snapshot_id"] for r in spark.table(f"{AGENT_SCHEMA}.{name}").select("snapshot_id").distinct().collect()} == {snapshot_id}
assert content_fingerprint(*read_gold(spark, CATALOG)) == source_fingerprint, "Source changed during setup; rerun before marking READY"

# Validate all numeric default substitutions using the actual Spark queries.
# AIDP UI must perform type validation separately; this evaluator is for notebook smoke tests only.
def test_query(tool, params):
    # Smoke tests may read the staging snapshot before it is made available to agents.
    query = tool["query"].replace("status = 'READY'", "status IN ('PREPARING', 'READY')")
    for parameter in tool["parameters"]:
        value = params.get(parameter["name"], parameter["defaultValue"])
        if type(value) is not int or not parameter["minimum"] <= value <= parameter["maximum"]:
            raise ValueError("Smoke-test parameters must be bounded integers")
        query = query.replace("{{" + parameter["name"] + "}}", str(value))
    if "{{" in query:
        raise ValueError("Unresolved SQL template variable")
    return spark.sql(query)

seed_account = published_accounts.filter((F.col("period_key") == latest_period_key) & (F.col("flagged_count") > 0)).orderBy(F.desc("flagged_gross_usd"), "account_id").first()
if seed_account is None:
    seed_account = published_accounts.filter(F.col("period_key") == latest_period_key).orderBy("account_id").first()
seed_account_number = int(seed_account["account_id"][3:])
smoke_rows = []
for tool in SQL_TOOLS:
    result = test_query(tool, {"period_key": latest_period_key, "account_number": seed_account_number, "dimension_code": 1})
    count = result.count()
    assert count <= tool["max_rows"], f"Tool exceeds hard SQL row cap: {tool['tool_name']}"
    if tool["tool_name"] != "get_priority_accounts":
        assert count > 0, f"Unexpected empty result: {tool['tool_name']}"
    smoke_rows.append({"tool": tool["tool_name"], "rows": count, "status": "PASS"})
publish_registry(smoke_rows, "sql_smoke_results", "tool")
publish(metadata_frame("READY"), "snapshot_metadata_sql")
display(HTML(table_html(smoke_rows, [("tool", "Tool query"), ("rows", "Rows"), ("status", "Spark SQL check")])))
print(f"Demo seed: period {latest_period_key}; account {seed_account['account_id']}; account_number={seed_account_number}")
print("Hero prompt: For the latest observed month, rank accounts by flagged gross exposure, investigate the top account, retrieve the applicable synthetic triage policy, and draft a USD analyst brief with citations and human-review steps.")
print("Setup READY. Next: ingest and test RAG independently, then build and test the no-code Agent Flow.")
account_monthly.unpersist(); portfolio_monthly.unpersist()

# %% [markdown]
# ## 8. No-code handoff
# 1. Check the source and demo schema in Master catalog. Confirm `snapshot_metadata_sql.status = READY`.
# 2. Upload `rag_corpus` TXT files into one managed/external volume folder. Create a Knowledge Base and ingest it.
# 3. Verify a RAG tool test returns the exact P1 thresholds and `[FS-POL-001 v1.1 §2]`; empty retrieval blocks hybrid readiness.
# 4. Create Message → Guardrails → one Supervisor → four Executors. Attach the registered SQL, RAG and Prompt tools.
# 5. Copy prompts and SQL configurations from the package or registry tables. Select available region/model and active compute.
# 6. Run acceptance cases, inspect traces, deploy/redeploy, and repeat the hero prompt in Playground.
#
# This notebook never creates the visual flow, Knowledge Base, deployment, remote tools or external actions.
