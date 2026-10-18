# Recreate the six-canvas OAC workbook

The workbook turns the verified native AILH publication into an executive snapshot, a fixed reference brief, trends, an investigation queue, exposure breakdowns and monthly comparisons. This is a rebuild recipe; the package does not contain an importable OAC workbook export.

**Demonstration dataset; amounts shown in INR.** Screening flags are not confirmed fraud. Use the [methodology](metrics-and-methodology.md) for metric interpretation and the [AILH publication steps](user-guide.md#9-optional-ailh-publication-and-oac) before creating datasets.

## 1. Establish the native source and connection

1. Verify both native Gold targets after publication, including full-row equality. Record each source Delta version, target owner, publication time and reconciliation status.
2. In OAC create/select an approved database connection to that AILH database. Use a read-only identity with SELECT access to the published native objects. Supply connection credentials through OAC's supported credential mechanism.
3. Test the connection, then create the datasets below from it. Replace `GOLD` in every SQL statement with the verified physical Oracle owner if it differs. The connection's display name is not necessarily the physical owner.
4. Keep all datasets on the same native publication. A successful connection does not establish that the data matches a historical screenshot.

The supplied queries contain only generic schema/table names and no personal endpoints, deployment identifiers or credentials. They use **Oracle SQL**, separate from the seven Spark agent-tool templates.

## 2. Create the four datasets

Suggested names match the reference workbook's functional roles; they are not required object identifiers.

| Dataset | Source | Grain / purpose |
|---|---|---|
| `TRANSACTION_ANALYTICS_AIDP_FS_GOLD` | Native `GOLD.TRANSACTION_ANALYTICS_GOLD` | Original account-month aggregates and reconciliation reference |
| `FRAUD_DETECTION_MODEL_AIDP_FS_GOLD` | SQL projection below of native transaction Gold | One transaction row; filterable snapshot, trends and type/location/score views |
| `FS_ACCOUNT_MONTH_RISK_AIDP_FS_GOLD` | [`account_month_risk.sql`](../sql/oac/account_month_risk.sql) | One account-month; exact totals, priority, portfolio rank and denominator |
| `FS_MONTHLY_RISK_REVIEW_AIDP_FS_GOLD` | [`monthly_risk_review.sql`](../sql/oac/monthly_risk_review.sql) | One month; complete portfolio, P1, concentration and calendar-aware change metrics |

For the last two, create a SQL-backed dataset and paste the corresponding complete query. Validate a preview before saving. The queries are self-contained: the monthly query includes the account-level logic, so it does not depend on a database view named after the account dataset.

For the transaction dataset, use this SQL projection to make row-level calculations and period labels explicit at the database layer:

```sql
SELECT ACCOUNT_ID,
       TRANSACTION_DATE,
       TO_CHAR(TRANSACTION_DATE, 'YYYY-MM') AS REPORT_MONTH,
       TRANSACTION_TYPE,
       MERCHANT_CATEGORY,
       LOCATION,
       AMOUNT,
       RISK_SCORE,
       IS_FRAUD,
       ABS(AMOUNT) AS GROSS_AMOUNT_INR,
       CASE WHEN RISK_SCORE > 60 THEN 1 ELSE 0 END AS RULE_FLAG,
       CASE WHEN RISK_SCORE > 60 THEN ABS(AMOUNT) ELSE 0 END AS FLAGGED_AMOUNT_INR,
       CASE WHEN RISK_SCORE <= 20 THEN '00-20'
            WHEN RISK_SCORE <= 40 THEN '21-40'
            WHEN RISK_SCORE <= 60 THEN '41-60'
            WHEN RISK_SCORE <= 80 THEN '61-80'
            ELSE '81-100' END AS SCORE_BAND
FROM GOLD.FRAUD_DETECTION_MODEL_GOLD
```

`IS_FRAUD` is retained for lineage, but visible labels should say rule flag or synthetic rule label. `REPORT_MONTH` is a sortable YYYY-MM attribute; `ACCOUNT_ID` stays text with leading zeros. Set transaction type, merchant category, location and score band as attributes. Never use source row counts from a joined monthly dataset as transaction counts.

Keep the transaction, account-month and monthly datasets as distinct analytical grains. Do not join complete monthly totals to transaction rows and sum them; that repeats each monthly measure once per transaction. If your OAC workbook requires dataset relationships for a particular interaction, define keys/cardinality deliberately, then validate every affected visual for fanout. This recipe uses visual-specific datasets and explicit filter scope instead.

## 3. Define the calculated measures and formats

In the transaction dataset/workbook, create the following measures. Expressions below use quoted field names; insert the corresponding dataset columns through OAC's expression editor so it adds any required dataset qualification. `RULE_FLAG`, `GROSS_AMOUNT_INR` and `FLAGGED_AMOUNT_INR` are the row-level SQL projection fields above.

| Visible measure | Exact expression / aggregation | Format |
|---|---|---|
| Transactions | `COUNT("ACCOUNT_ID")` | Integer, thousands separator, 0 decimals |
| Active accounts | `COUNT(DISTINCT "ACCOUNT_ID")` | Integer, thousands separator, 0 decimals |
| Gross activity INR | `SUM("GROSS_AMOUNT_INR")` | Currency INR/₹, 2 decimals |
| Net activity INR | `SUM("AMOUNT")` | Currency INR/₹, 2 decimals; preserve negative sign |
| Rule flags | `SUM("RULE_FLAG")` | Integer, thousands separator, 0 decimals |
| Flagged gross INR | `SUM("FLAGGED_AMOUNT_INR")` | Currency INR/₹, 2 decimals |
| Flag rate (%) | `100.0 * SUM("RULE_FLAG") / NULLIF(COUNT("ACCOUNT_ID"), 0)` | Number, 2 decimals; label explicitly `%` |
| Average rule score | `AVG("RISK_SCORE")` | Number, 2 decimals; no percent sign |

The rate expression already returns a value from 0 to 100. Do not apply a percentage format that multiplies by 100 again. If you intentionally use OAC's ratio-to-percent formatter, define a separate ratio without the `100.0` factor and verify its displayed value against the reference.

Use **native abbreviated display in millions** for large currency KPI cards (for example ₹31.64M) and full two-decimal currency in tables/tooltips. The reference uses millions; do not divide an already abbreviated measure again or relabel a value as crore without a separately validated conversion. Keep the underlying amount unchanged.

### Account-month measures

The account SQL exposes `TRANSACTION_COUNT`, `GROSS_ACTIVITY_INR`, `NET_ACTIVITY_INR`, `AVG_RULE_SCORE`, `RULE_FLAGS`, `FLAGGED_GROSS_INR`, `FLAG_RATE_PCT`, `HIGH_VALUE_FLAGS`, `DEMO_PRIORITY`, `EXPOSURE_RANK` and `MONTH_FLAGGED_GROSS_INR`.

- Use `ACCOUNT_ID` + `REPORT_MONTH` as the row grain. Counts are integers, money has two decimals, `FLAG_RATE_PCT` has two decimals and priority is a categorical label.
- Treat `EXPOSURE_RANK` as an ordinal/nonadditive field: use the row's value, or MAX at exact account-month grain, rather than SUM.
- `MONTH_FLAGGED_GROSS_INR` repeats the whole month's denominator on every account row. At a single month use MAX for that denominator, not SUM.
- To aggregate multiple accounts in one month, compute `100.0 * SUM(RULE_FLAGS) / NULLIF(SUM(TRANSACTION_COUNT),0)` rather than averaging `FLAG_RATE_PCT`.
- To compute an average score across account rows, use `SUM(AVG_RULE_SCORE * TRANSACTION_COUNT) / NULLIF(SUM(TRANSACTION_COUNT),0)`; the simple mean of account means is not transaction-weighted.

### Monthly measures

The monthly SQL returns exact fields, already calculated at month grain:

| Field | Meaning / display |
|---|---|
| `TRANSACTIONS`, `ACTIVE_ACCOUNTS`, `RULE_FLAGS`, `P1_ACCOUNTS` | Integer counts |
| `GROSS_ACTIVITY_INR`, `NET_ACTIVITY_INR`, `FLAGGED_GROSS_INR`, `TOP10_FLAGGED_GROSS_INR` | INR/₹, 2 decimals; native M abbreviation only on large cards |
| `FLAG_RATE_PCT`, `TOP10_SHARE_PCT` | Number, 2 decimals, explicit percent label |
| `TRANSACTIONS_MOM_PCT`, `GROSS_MOM_PCT`, `FLAGGED_MOM_PCT` | Signed percentage change, 2 decimals; already multiplied by 100 |
| `FLAG_RATE_CHANGE_PP` | Signed percentage-point change, 2 decimals, `pp` label |

At one selected month, use its single row rather than summing rates. Across months, monthly active accounts are not annual unique accounts. The change query checks that the LAG row is the preceding calendar month; missing/first-month comparisons stay NULL. Do not convert NULL to zero.

## 4. Set the canvas and header once, then duplicate

Create a workbook, for example `FS_EXECUTIVE_DASHBOARDS`. Create the first canvas, then configure its properties:

| Property | Value |
|---|---|
| Layout | **Auto Fit** |
| Width | **Screen** |
| Height | **Screen** |
| Main header | `Financial services executive overview`, **28 px** |
| Canvas subtitle | Canvas-specific title below, **16 px** |
| Disclosure line | `Demonstration dataset; amounts shown in INR. Screening flags are not confirmed fraud.`, **12 px** |
| Oracle wordmark | [`oracle-wordmark.png`](../media/brand/oracle-wordmark.png), displayed **160 × 21 px**, preserve proportions |

Place the image at the top left and the three-line text header beside it. Use a light warm-neutral background, dark readable text, modest borders and Oracle Red as an accent. Native charts remain editable; no custom JavaScript or external dashboard app is required.

Duplicate this header/layout for all six canvases. Keep the header shallow enough that KPI cards and charts remain readable. Full-width monthly charts need sufficient space for complete YYYY-MM labels. Tables can retain internal scrolling within Auto Fit; do not shrink their text until all rows fit. Test full-width preview after closing editing panels. The historical desktop layout was inspected after reload; mobile breakpoints were not tested.

## 5. Build the six canvases

### Executive snapshot

Subtitle: `Executive snapshot`. Use a reporting-month selector on the snapshot cards and queue. Use the transaction dataset for these eight KPI cards:

```text
Transactions | Active accounts | Gross activity INR | Net activity INR
Rule flags   | Flag rate (%)   | Flagged gross INR  | Average rule score
```

Lay out the cards as two rows of four, or an equivalent readable Auto Fit grid. Add an annual line chart `Activity and screening · 2024 · Whole portfolio`, with REPORT_MONTH ascending and Transactions/Rule flags as series. Exclude the single-month selector from this annual chart; if you apply an account selector to it, change the title to disclose that filtered population.

Add a small account-month queue table with Account, Flagged gross INR and Demo priority, filtered to one report month, `RULE_FLAGS > 0` and `EXPOSURE_RANK <= 10`, sorted by exposure rank ascending. Keep its exposure-rank scope whole-portfolio unless explicitly recalculated.

For the frozen December reference, the cards should reconcile to 12,699 transactions; 4,436 active accounts; gross INR 31,642,312.97; net INR 20,071,594.45; 4,934 flags; 38.85% displayed flag rate; and flagged gross INR 12,547,752.55. Validate average score directly from the same source; a rounded score is not a probability. A newly generated source should match its own SQL results instead of these historical figures.

### Executive brief

Subtitle: `Executive brief — validated snapshot for December 2024` **only when displaying the frozen reference**. For other data use an accurately dated, scoped title. Build a readable text panel with:

1. Period/source and INR assumption.
2. Activity and screening KPIs from the reconciled monthly row.
3. P1 count and exposure concentration, using the complete portfolio denominator.
4. Exact screening rule and P1 predicate.
5. Analyst-review recommendation, missing information and draft/action boundary.

The reference brief is fixed December 2024 text. It does not automatically update when filters change. Exclude it from misleading filter interactions and mark it **Fixed reference narrative — December 2024**. To create a dynamic brief, build and separately validate a supported data-driven narrative; this package does not supply such an OAC narrative automation.

Use the [reference snapshot](../data/reference-snapshot.json) for the fixed numbers, including 528 P1 accounts and top-ten flagged gross INR 236,847.35, representing 1.887567905536996% of portfolio flagged gross. State that this is exposure concentration, not confirmed fraud loss. End with `Human review required. No external action executed.`

### Activity and risk trends

Subtitle: `Activity and risk trends`. Use transaction measures by REPORT_MONTH for the full selected annual/window scope. Create line charts for:

- Transactions and rule flags.
- Gross activity and flagged gross, with clear INR axis units.
- Flag rate (%) and, if useful, average rule score in separate appropriately labeled visuals rather than a misleading shared scale.

Keep months ascending with full YYYY-MM labels. Set the month-window filter independently of the snapshot's single-month selector. Preserve missing calendar months as gaps; the supplied monthly SQL does not synthesize absent months. If the OAC categorical axis compresses missing months, add an explicit gap note/table or a separately validated calendar scaffold; never fill missing data with zero silently.

An account filter can be supported by transaction measures if all relevant visuals inherit it consistently. Reconcile a known account's counts and denominator before using it in a presentation.

### Investigation queue

Subtitle: `Investigation queue`. Use the account-month dataset with one REPORT_MONTH, `RULE_FLAGS > 0`, and `EXPOSURE_RANK <= 10`.

Add the table columns in this order:

```text
ACCOUNT_ID | EXPOSURE_RANK | DEMO_PRIORITY | TRANSACTION_COUNT |
RULE_FLAGS | FLAGGED_GROSS_INR | FLAG_RATE_PCT | HIGH_VALUE_FLAGS
```

Sort by EXPOSURE_RANK ascending; this preserves the SQL ordering of flagged gross descending, flags descending and account ID. Add a bar chart of flagged gross by ranked account, sorted in the same order. Use restrained P1/P2 conditional formatting with text labels so meaning is not color-dependent.

The frozen first account is `ACC00004535`, with flagged gross INR 28,008.03. This is an exposure rank, not a predicted-fraud rank. An account selector filters a precomputed whole-month rank; it does not recompute the top ten of the selected subset.

### Risk exposure breakdown

Subtitle: `Risk exposure breakdown`. Use the transaction dataset with one selected report month. Add:

- Bar chart: transaction type versus flagged gross INR.
- Bar chart: source location label versus flagged gross INR.
- Bar chart: SCORE_BAND versus Transactions, ascending `00-20`, `21-40`, `41-60`, `61-80`, `81-100`.

Include transactions, flags, full gross and flag rate in supporting tables/tooltips where useful. Each breakdown partitions the same source population. Never add type totals to location totals. Location labels are not KYC residence or verified geography; transaction type is not a verified channel taxonomy. Score bands describe random synthetic source scores.

### Monthly changes

Subtitle: `Monthly changes and concentration`. Use only the complete monthly dataset. Add a monthly table containing report month, transactions, gross, flagged gross, flag rate, P1 accounts, top-ten flagged gross, top-ten share, the three MoM percentage changes and flag-rate change in pp. Add line charts for selected change/concentration fields with distinct units and explicit labels.

Keep this canvas whole-portfolio and exclude account filters. The frozen December comparison displays approximately +4.04% transactions, +3.43% gross, +1.23% flagged gross and −1.03 percentage points flag rate. These are descriptive changes, not causal effects or model impact. First/missing-prior-month comparisons remain unavailable.

## 6. Make filter scope explicit

| Control/content | Intended scope |
|---|---|
| Snapshot month selector | Snapshot KPI cards, small queue, full queue and exposure breakdowns |
| Annual/window month filter | Trends; keep history visible independently of the single-month selector |
| Account selector | Only transaction/account-level visuals intentionally configured and tested for it |
| Queue `EXPOSURE_RANK <= 10` | Queue visuals only; never constrain portfolio KPI/concentration denominators |
| Monthly change/concentration dataset | Whole portfolio; exclude account filters |
| Executive brief reference text | Fixed December 2024; visibly exclude from dynamic filter claims |

With multiple datasets, similarly named columns do not prove that a control filters them all correctly. Inspect each visual's filter assignments. A top-ten selection must not turn the denominator into top-ten exposure and display 100% concentration.

For a filtered-population ranking/concentration variant, change the underlying SQL so the selected account population is filtered **before** account ranking and monthly denominator calculation, then validate it as a separate variant. The shipped SQL intentionally computes whole-month portfolio ranks and denominators.

## 7. Reconcile, save and reload

1. Select one observed month and whole-portfolio scope. Compare every headline metric with direct native SQL from the same publication.
2. Verify queue order, first account, P1/P2 boundary, full account totals and top-ten flagged-gross sum/share. Verify score 60 is not flagged and preserve the complete P1 OR/AND predicate.
3. Test one existing account on the supported transaction visuals, compare direct SQL, then restore All. Confirm whole-portfolio monthly/concentration and fixed reference narrative do not silently inherit that account selection.
4. Test first-month and missing-prior-month behavior; never convert NULL comparison to zero. Inspect annual labels at full preview width.
5. Save, leave edit mode, reload and revisit all six canvases. Confirm header font sizes, wordmark dimensions, selected month/filter scope, sort order, KPI values and brief text persisted.
6. Review screenshot exports for readable labels and absence of private hostnames/user catalog paths. Record mobile checks only if performed; desktop Auto Fit does not prove mobile usability.

For a different source generation, keep the calculations and checks, refresh the dates/narrative and record its own reconciled results. OAC publication correctness and the agent's SQL/RAG/hybrid acceptance remain separate evidence gates.

Related: [user guide](user-guide.md), [architecture](architecture.md), [metrics](metrics-and-methodology.md), [hosted acceptance](hosted-acceptance.md).
