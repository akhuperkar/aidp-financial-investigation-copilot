# USD denomination release

The current scenario uses USD, policy corpus version **1.1** and rule version **FS-TRIAGE-1.1**. Native Gold has no currency column. Its existing amount values are interpreted as US dollars; this release applies **no exchange rate, numerical rescaling, transaction regeneration or model retraining**.

The source Gold contracts keep generic `amount`, `total_amount` and `avg_amount` names. Derived dashboard/agent fields use `_usd`, including `gross_amount_usd`, `net_amount_usd`, `flagged_gross_usd`, `high_value_usd` and `p1_account_exposure_usd`. Amount thresholds remain 5,000 and 10,000. Counts, source amounts, queue order and rule flags remain the same on an unchanged source snapshot. A semantic snapshot ID changes because currency and rule version enter its hash.

## Apply to an existing environment

1. Save the current source versions and serving metadata. Keep the unseeded medallion generator and ML training cells unexecuted during this migration.
2. Update the dashboard and agent setup notebook sources. Preserve tenant-specific catalogs, connection and volume configuration.
3. Preserve the **existing serving snapshot** if it may differ from current Gold. Initialize only the new setup definition cells (`SQL_TOOLS`, `RAG_DOCUMENTS`, `PROMPTS`, `ACCEPTANCE_CASES`), then run [the existing-snapshot migration adapter](../scripts/migrate_existing_snapshot_to_usd.py) in that Spark session. Do not run the setup Gold-read or materialization cells for this migration. The adapter keeps write-once rollback copies, stages replacements, and checks exact full-row parity before changing metadata to `READY`, `currency_assumption=USD`, `rule_version=FS-TRIAGE-1.1`. A normal setup rebuild against current Gold is a separate source refresh and can change the data set.
4. Replace all seven SQL tools from `config/sql_tools.json`; replace node instructions from `agents/node-configurations.json`. New field names and tools must move together.
5. Replace the Knowledge Base corpus with all eight `rag_corpus/` version-1.1 documents, then ingest. Retire old corpus chunks from the active KB so contradictory denomination versions cannot be retrieved together. Verify actual retrieved source chunks and version markers.
6. Update Agent Card metadata to version 1.1.0, redeploy the flow and refresh its AI Registry entry. Start new Hub and Streamlit sessions so prior conversation context cannot supply the former denomination.
7. Update OAC measure labels, currency formats, titles, captions and narrative text to USD; preserve AutoFit canvas width/height, layout and numeric values. Refresh data only when necessary for a changed semantic schema.
8. Compare transactions, accounts, gross, net, flagged gross, queue order and P1 counts with the preserved numeric baseline. Test SQL, policy and hybrid requests separately. Replace screenshots only after the displayed USD values have been checked.

## Historical evidence

The [pre-migration archive](../reference/archive-inr-2026-10-18/README.md) preserves original files and screenshots with their original denomination. It is provenance, not new USD verification. The active [reference snapshot](../data/reference-snapshot.json) separates the original numeric-verification date from the later denomination update. Hosted acceptance status must be recorded independently; a text migration does not prove a deployed workflow passed.

## Migration adapter and prompt source

The one-time adapter deliberately contains legacy column/currency/version names so it can recognize and transform an earlier deployment. Those compatibility strings do not define the current contract. It preserves original preparation timestamps and source fingerprint, computes the new semantic snapshot ID, and refreshes all four configuration registries. It never reads Gold. Stop concurrent setup writers, retain the `*_pre_usd_20261018` rollback tables, and use fresh client sessions after success. A failure leaves metadata `PREPARING`; inspect and retry rather than forcing `READY`. Multi-table replacement is sequential and cannot revoke an already in-flight request.

`agents/node-configurations.json` is the reviewed source of agent/tool behavior and model parameters. The builder embeds those exact definitions in setup cell 12 and exports `config/prompts.json` and `agents/prompts/`; the RAG preamble is included alongside the Prompt tool and retained Guardrails guidance. The Brief gateway uses the literal `evidence_packet` parameter and returns the Prompt tool's Markdown unchanged. To refresh only the prompt registry in an existing deployment, initialize definition cell 12 and publish `PROMPTS` to `prompt_registry`; no data materialization is needed.
