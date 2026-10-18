# Metrics, methodology and reproduction

The analysis prioritizes transaction-screening review using complete monthly aggregates, bounded transaction evidence and retrieved fictional policies. It does not measure confirmed fraud, recovered money or a production model's detection performance.

**Demonstration dataset; amounts shown in INR.** There is no currency column in the source. INR is a display assumption without foreign-exchange conversion. Original transaction-type and US/Online/ATM location labels are retained.

## Reference data and snapshot separation

The 17 October 2026 [Gold/OAC reference](../data/reference-snapshot.json) has 149,658 transaction rows, 52,735 account-month rows and 5,000 accounts over January–December 2024. Both source Gold tables were read at Delta version 4 for the verified native publication.

| December 2024 reference measure | Value |
|---|---:|
| Transactions | 12,699 |
| Active accounts | 4,436 |
| Gross activity | INR 31,642,312.97 |
| Signed net activity | INR 20,071,594.45 |
| Rule-flagged transactions | 4,934 |
| Transaction-count flag rate | 38.853453027797464% |
| Flagged gross exposure | INR 12,547,752.55 |
| P1 accounts | 528 |
| Top-ten flagged gross | INR 236,847.35 |
| Top-ten share of portfolio flagged gross | 1.887567905536996% |
| First exposure-ranked account | ACC00004535 |
| First account's flagged gross | INR 28,008.03 |

These values are a frozen reference, not assertions about a new run. Earlier deployed-agent/Streamlit records use a different snapshot and different December totals. Do not combine their queue, evidence, percentages or screenshots with this OAC reference. A matching month alone does not establish a matching source.

For every comparison, retain consumer path, source versions/fingerprint, semantic `snapshot_id` where applicable, period, account/filter scope, rule version, timezone and preparation time. Source table version 4 is independent of an agent `snapshot_id` and an Agent Card version.

## Three levels of reproduction

1. **Schema and invariant reproduction.** Run the supplied unseeded medallion generator, then verify contracts, aggregation formulas, label boundaries, distribution maps and the seven query behaviors. Exact counts/rankings may differ. This is the normal clean-environment path.
2. **Seeded local calculation reproduction.** The local adapter explicitly seeds Python's generator with `42`, executes the original data/transformation cells and runs the two consumer notebooks. It uses local Spark 3.5.3, translates catalog names and writes Parquet instead of Delta. The seed controls this test fixture; it does not recreate the historical cloud source or validate the cloud platform.
3. **Exact frozen-output reproduction.** Preserve the original transaction dataset and its corresponding account-month Gold, with immutable versions or exported content and provenance. Read the same versions, rules, timezone and filters. The unseeded source notebook and saved output cells alone cannot regenerate the exact 149,658-row snapshot. A newly added seed cannot recover a random sequence that was never recorded.

The original source notebook and archived materials are retained under [`reference/`](../reference/). Their provenance hashes describe archived bytes. Publicly sanitized or revised runnable copies can have different hashes; use the current package's manifests rather than treating a historical package manifest as proof of current file integrity.

## Generator and data preparation

The source generator creates identifiers `ACC00000001` through `ACC00005000`, with 10–50 transactions per account. It chooses a 2024 timestamp, transaction type, merchant category and location label. Deposits and transfers receive positive amounts; ATM, withdrawals and payments receive negative amounts according to the source convention. A transfer has no persisted destination/counterparty, so it cannot establish network movement or inter-account flow.

`risk_score` is sampled independently as an integer from 0 to 100. Silver filters rows missing account, timestamp or amount, and adds month/day/hour fields. Its illustrative `data_quality_score` is partly computed from the random risk score; it is not an independently validated data-quality assessment.

Gold contains one account-month aggregate table and one transaction-feature table. The actual persisted schema matters: DataFrame overwrites omit some timestamp columns declared in the original DDL. Consumers check required columns, numeric types, finite amounts, identifier shape, timestamp type, score range, rule-label consistency, nonempty inputs and unique account-month grain.

## Metric definitions

All formulas apply to the selected period and account population. Aggregate amounts use full source rows; displayed money is rounded to two decimals.

| Measure / field | Definition | Interpretation |
|---|---|---|
| `transaction_count` | Count of transaction rows, including repeated content | Activity count |
| `active_accounts` | Distinct accounts with transactions in the selected month | Nonadditive across months |
| `gross_amount_inr` | `SUM(ABS(amount))` | Total transaction magnitude |
| `net_amount_inr` | `SUM(amount)` | Signed activity; not cash/account balance |
| `positive_amount_inr` | Sum of positive amounts | Source-sign activity |
| `negative_magnitude_inr` | Sum of absolute negative amounts | Source-sign activity magnitude |
| `rule_flag` / `is_fraud` | 1 only if `risk_score > 60` | Synthetic screening label |
| `flagged_count` | Sum of rule flags | Flagged transaction count |
| `flagged_gross_inr` | Sum of absolute amounts where score > 60 | Flagged exposure; not total gross, loss or probability |
| `flagged_rate_pct` | `100 × flagged_count / transaction_count` | Count percentage; not share of monetary value |
| `high_value_flagged_count` | Count where score > 60 and absolute amount ≥ 5,000 | Inclusive amount threshold |
| `very_high_value_count` | Count where score ≥ 85 and absolute amount ≥ 5,000 | Both conditions apply to the same transaction |
| `avg_risk_score` | Mean source score; portfolio average is transaction-weighted | Random score average; not calibrated risk |
| `p1_accounts` | Count of account-months meeting P1 | Distinct accounts within a month |
| Top-ten concentration | Sum of top-ten account flagged gross / complete portfolio flagged gross × 100 | Monetary exposure share; separate from flag rate |

Where portfolio flagged gross is zero, a concentration percentage is undefined; report unavailable rather than divide by zero. Gross and signed net must remain separate: equal positive and negative activity can net to zero while retaining substantial gross exposure.

### Priority and queue ordering

The fictional rule version is `FS-TRIAGE-1.0`:

```text
flagged transaction = risk_score > 60

P1 account-month = flagged_gross_inr >= 10000
                   OR exists transaction where
                      risk_score >= 85 AND abs(amount) >= 5000
P2 account-month = has a flagged transaction and is not P1
P3 account-month = has no flagged transaction
```

Score 60 is not flagged; 61 is flagged. Score 85 alone does not trigger the second P1 alternative if the amount is INR 4,999.99. INR 5,000 meets the amount threshold. INR 10,000 of **flagged** gross meets the first P1 alternative.

The queue includes only accounts with `flagged_count > 0`. Its stable order is `flagged_gross_inr DESC, flagged_count DESC, account_id`. The top ten are exposure-ranked, not ranked by predicted loss or necessarily grouped by P1 before P2. Use the actual first returned account; do not hard-code an account from a different snapshot.

### Time, filters and dimensionality

`period_key` is integer YYYYMM; `month_year` is YYYY-MM. Zero means resolve the latest **observed** month, not the current calendar month. Resolve it once and reuse the explicit returned period. Preserve an unavailable requested period and return no data. Record the Spark session timezone because timestamp-to-month extraction depends on it.

The trend tool returns at most twelve observed monthly rows ending at an available requested month. Missing months remain gaps; a previous observed row is not automatically the previous calendar month. The dashboard's month-over-month comparison uses the immediately preceding calendar month. Do not sum monthly active-account counts to claim annual unique customers.

Exposure mix dimension 1 is transaction type; dimension 2 is source location label. Both represent the same transaction population, so summing both dimensions doubles the total. Labels do not establish channel, residence or verified geography. Dashboard account filters must apply to numerators and denominators alike.

## Reconciliation and numerical precision

The consumer notebooks independently aggregate transaction Gold and join it to account-month Gold across **all** keys. They reject missing/duplicate keys and differences in transaction counts, signed totals, averages, flags and category-count maps. Amount comparisons allow the source's decimal rounding tolerance of INR 0.02; score-average tolerance is `1e-8`. These are calculation-contract checks, not detection-accuracy tests.

The setup checks that evidence multiplicities sum to the source row count and that multiplicity-weighted gross agrees with complete portfolio gross within INR 0.02. It verifies all semantic data tables share one snapshot and that the source fingerprint is unchanged before publishing READY.

The AILH publisher independently pins both Delta versions, normalizes the native contract and checks schemas, counts and exact decimal totals. With `verify_full_rows=True`, a bidirectional `exceptAll` compares the complete normalized row multisets, including duplicate multiplicities, canonicalized JSON and timestamps. Passing counts/totals alone is weaker than full-row equality. Version pinning stabilizes each table; it does not prove both tables came from a single atomic upstream batch.

The verified native publication used 52,735 account-month rows and 149,658 transaction rows. Initial creation/unchanged-data reuse succeeded. Changed-data replacement remains unverified and can fail `DATA_ACCESS_LAYER_0068`. Optional native DDL/index execution was not exercised. Both source tables remained unclustered because this runtime could not enable clustering through ALTER.

## Evidence groups and citations

There is no unique transaction ID in the source. `transaction_evidence_sql` groups identical selected source columns and preserves `duplicate_multiplicity`. `source_row_fingerprint` identifies content, not a unique transaction. Do not deduplicate it to discard repeated source rows.

The queue returns at most ten accounts; transaction evidence returns at most twenty groups. A report may show five rows. Record displayed rows, returned rows, full candidate/group counts and cap separately. Four returned groups out of four observed groups with a cap of twenty is **not** “four of twenty transactions.” Unflagged evidence rows are allowed. Complete account exposure comes from `get_account_snapshot`, never from summing the bounded sample.

Numeric claims cite the actual SQL tool, explicit period/account and snapshot, for example `[SQL:get_account_snapshot | YYYYMM | ACC######## | snapshot]`. Policy claims cite an actually retrieved document, version and explicit section header, for example `[FS-POL-001 v1.0 §2]`. Preserve returned source references without inventing filenames, section numbers, chunk IDs or similarity scores. A policy summary can omit a clause; inspect actual passages and adjacent continuations.

## What the ML example measures

The label is constructed as `is_fraud = 1 if risk_score > 60 else 0`; `risk_score` itself is random. The pipeline indexes transaction type, merchant category and location; assembles amount, month, day-of-week, hour and category indices; scales features; and trains a random forest with 100 trees and maximum depth 10. It uses an 80/20 split with `seed=42` and prints ROC AUC and a confusion matrix for this artificial label.

The feature list excludes `risk_score`. This avoids directly passing the threshold variable as a feature, but does not turn random labels into independently confirmed outcomes. A split seed does not seed the original generator or guarantee deterministic training across runtime versions. No trained-model predictions/probabilities are persisted to the Gold tables consumed by the agent, and the agent's queue is computed by SQL rules. Printed model evaluation cannot support a claim of reduced fraud loss, operational precision/recall or production detection value.

## Decision limits and validation status

The dataset has no independently confirmed fraud outcomes, realized losses, recoveries, balances, KYC, counterparties or persisted model scores. All policies are fictional. Proposed analyst steps are draft guidance; no external action or approval workflow is implemented.

Historical user-reported Agent Hub successes, local calculation checks, native publication verification and client transport checks establish different things. The recorded Streamlit hybrid result failed evidence-row reconciliation despite a completed task and preserved context. Root cause remains unverified. Read [hosted acceptance](hosted-acceptance.md) before claiming current end-to-end correctness; the package does not claim an all-pass hosted run.
