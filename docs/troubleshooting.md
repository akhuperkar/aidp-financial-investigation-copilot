# Troubleshooting

Diagnose the failing layer before changing data or deployment settings. A notebook, a tool test, a playground run, a published card and a final answer in Agent Hub are different checkpoints.

Record UTC time, selected environment/version, failing operation, exact error, explicit reporting period and whether a backend task continued after the UI failed. Keep real endpoint URLs, deployment IDs, sessions and credentials in an approved private diagnostic record; publish a sanitized summary only.

## Notebook and source failures

| Symptom | Check and recovery |
|---|---|
| `spark` is undefined | Use AIDP Workbench with the intended attached Spark cluster. Local validation uses its own adapter; the cloud notebooks are not plain Python scripts. |
| Gold table missing or empty | Confirm catalog/schema, read grants and completion of the medallion source. Inspect both Gold tables before running consumers. |
| Schema differs from original CREATE TABLE | Inspect `printSchema()` on persisted data. Source DataFrame overwrites omit some declared timestamp fields; consumers validate the actual contract. Do not invent missing timestamps. |
| Gold account-month reconciliation fails | Stop downstream publication. Compare keys, counts, signed totals, averages and category maps. Rebuild both Gold tables from a consistent Silver snapshot in a controlled refresh. |
| Totals differ from screenshots | Check source versions/fingerprint, consumer path, month, timezone and account filters. The original generator is unseeded; new runs differ from the frozen reference. |
| `snapshot_metadata_sql` stays PREPARING | Read the setup notebook's first failed assertion/query. Complete the entire setup successfully; do not manually mark an inconsistent snapshot READY. |
| Unsupported `CLUSTER BY` / ALTER | Inspect actual runtime and table layout. Preserve existing unclustered Gold; do not rebuild or upgrade protocols merely to reproduce the picture. Native Oracle AILH tables do not use Delta liquid clustering. |
| Local Spark cannot start | Check Java 17, `AIDP_JAVA_HOME`, the Python/PySpark versions and loopback networking. The runner uses a temporary local warehouse and its own notebook kernel. |
| Local validation appears to prove cloud behavior | It does not. The fixture translates catalog names, substitutes Parquet and skips source clustering/model training. Run the hosted acceptance gates separately. |

If a source changes during setup, complete the upstream refresh first and rerun setup. Reusing a previous READY record with newer data can produce a plausible but inconsistent answer.

## SQL tool and routing failures

| Symptom | Check and recovery |
|---|---|
| Test tab disabled | Confirm active AI Compute is attached to the flow. Spark SQL also needs its selected Spark cluster running. |
| Tool cannot discover `finance.agent_demo_fs` | Select Spark SQL and the correct standard catalog/schema. Verify grants and direct notebook reads with the same intended identity. |
| UI offers only Oracle SQL | Verify the tenant feature/version. The supplied queries target Spark. An Oracle route needs compatible native semantic tables, translated syntax and independent tests. Two native Gold tables alone do not supply the agent surface. |
| Docs seem to require external catalogs only | The current tool page's overview and detailed SQL section disagree. The detailed section describes both dialects. Use an actual tool Test to establish your tenant's available path. |
| No context row | Setup is not READY, identifiers point to another schema, or read access is missing. Stop the investigation until fixed. |
| Valid explicit period returns no rows | Check observed coverage. Preserve the requested period; never silently fall back to latest. `0` is the deliberate latest-month sentinel. |
| A numeric account returns no rows | Convert an actual `ACC########` suffix to an integer and preserve the period. Do not infer that default account 1 exists in every month. |
| Queue/exposure numbers look wrong | Compare exact field names. `flagged_gross_usd` is flagged exposure; `gross_amount_usd` is total gross activity. Preserve SQL ordering and signs. |
| Evidence rows do not total to monthly exposure | Evidence is capped/grouped and can include unflagged rows. Read complete totals from `get_account_snapshot`; retain multiplicity and full-group counts. |
| Malformed numeric inputs are accepted | Block rollout and add/enforce deterministic parameter validation appropriate to the execution path. Descriptions, casts and local smoke validation do not enforce hosted integer bounds. Keep the execution principal SELECT-only. |
| Combined tools return different snapshots | Stop the combined answer, finish one refresh, and start a new investigation on one READY snapshot. |

Do not solve a tool problem by granting the agent broad write privileges. A backend success followed by a UI timeout requires correlation before resubmitting; the original request may still be running.

## RAG and briefing failures

| Symptom | Check and recovery |
|---|---|
| No relevant policy chunks | Confirm the eight files, selected KB, ingestion Job Run, embedding setup and data-source folder. Publishing `rag_document_manifest` is not ingestion. |
| P1 rule drops score ≥85 or amount ≥5,000 | Query the complete section-2 sentence and inspect adjacent chunks/headers. Tune chunk size/overlap/retrieval count, reingest if needed and rerun the targeted test. |
| Citation says §3 for a section-2 continuation | A header labels following text; a chunk index is not a section number. Verify continuity against the actual source before citing. |
| A revised policy and old rule both appear | Check superseded KB content and ingestion replacement behavior. Preserve version/effective scope and remove conflicting material through the supported lifecycle. |
| Tool summary conflicts with source chunks | Use the actual returned passages as evidence. If required clauses are missing, disclose the gap and withhold policy conclusions. |
| Prompt variable unresolved or missing | Use the current String parameter `evidence_packet` and template `{{evidence_packet}}`. Older HTML/registries may use `evidence_json`; do not mix versions. |
| Prompt/guardrails rejects a handoff | Check the literal packet: facts, exact rows, source excerpts and status only. Keep instructions in node/template settings. Report the error; do not obfuscate rejected content or weaken guardrails to force a brief. |
| Formatter invents transaction rows | Compare input packet, Prompt result and final supervisor output field-by-field. Withhold the brief; capture a sanitized mismatch record. Closed-world instructions do not substitute for verification. |
| A small request invokes every specialist | Reapply current routing instructions. Portfolio, account and document-only questions should take their bounded paths. |

The recorded Streamlit hybrid follow-up completed transport and retained context, but its transaction rows conflicted with reference evidence for the same account, period and snapshot. Root cause is unverified. Reconcile direct SQL results, executor handoff, Prompt input/output and final response as described in [hosted acceptance](hosted-acceptance.md); do not assume the client or source caused the mismatch.

## Deployment, card and Agent Hub

| Symptom | Check and recovery |
|---|---|
| Playground works; deployed behavior is old | Confirm the reviewed flow was redeployed to hosting compute. Playground attachment and deployed compute are separate. |
| Registry entry exists; Hub invocation fails | Test a minimal capability question, then focused SQL, then hybrid. Registration is discovery, not execution proof. |
| Card verifies; request is 401/403 | Confirm the deployment-approved auth mode, selected identity and invocation permissions. Card access can require less permission than execution. |
| Hub stops before backend completes | Record UTC timing and private correlation/task IDs, then inspect gateway/Hub/backend evidence. Separate response-delivery failure from backend failure. Do not claim a root cause without correlation. |
| A trace export has only the root node | It cannot establish every inner tool call. Obtain tool-level inputs/results or state that inner routing is unverified. |
| Large answer fails while focused SQL works | Compare duration, payload and tool scope. Use bounded evidence and concise responses. A longer timeout may help diagnose delivery, but cannot fix wrong values or unsupported policy. |
| Real endpoint missing from draft card | Retrieve the published endpoint/card from AIDP after deployment. Do not upload an empty-URL draft as the live registry card. |

## Streamlit client

Run from the repository root in the configured virtual environment:

```bash
source .venv/bin/activate
python -m streamlit run apps/copilot/app.py --server.port 8501 --server.address 127.0.0.1
```

| Symptom | Check and recovery |
|---|---|
| `ModuleNotFoundError: oci` | Install `requirements/oci.txt` into this same venv for OCI authentication. OAuth does not need that optional SDK. |
| Local OCI profile loads but auth fails | Check the selected profile/identity and deployment auth configuration. A security-token profile needs its matching key and unexpired token file. Do not assume DEFAULT is correct. |
| AIDP URL rejected | Copy the actual AIDP Chat, A2A or Agent Card URL. Arbitrary PAF/console URLs are not valid A2A endpoints. |
| Card protocol mismatch | This adapter expects A2A 0.3.0 JSON-RPC. Use the matching supported deployment/protocol or update the adapter with tests. |
| DNS/connect timeout | Check endpoint spelling, VPN, DNS/routing and host access from the machine running Python. |
| TLS verification failure | Correct the server certificate/CA chain and hostname, or set the approved provider-specific CA bundle. External TLS verification stays enabled. |
| 302 redirect or HTML login page | Check copied route and supported auth flow. Neither is a successful agent response; the clients refuse redirects. |
| PAF 404/401 | Check installation version, agent type, ID, route and its supported API-key/cookie mode. PAF credentials are unrelated to AIDP credentials. |
| Follow-up loses context | Inspect returned AIDP context or PAF room and the same endpoint/identity. For PAF set `PAF_ROOM_PATH` only after inspecting the real envelope. |
| Table/Visualization empty but Markdown present | The response may have narrative text only. Those views require actual structured rows; do not manufacture chart data. |
| History cannot open | Set `AIDP_HISTORY_DB` or `PAF_HISTORY_DB` to a writable SQLite path, then restart. Preserve local access controls for saved raw responses. |
| Customer name changes but title does not | Clear the nonempty Assistant title override and apply connection settings. Apply Customer branding again. |
| Port 8501 occupied | Identify the existing process and stop/reuse it intentionally. Do not silently replace an unrelated service. |

The app does not load `.env`. Restarting resets active forms/connections but preserves SQLite histories. Provider/profile changes disconnect and reset active context. Local history deletion does not erase remote records. Requests are not automatically retried after submission failures.

## AILH publication

| Symptom | Check and recovery |
|---|---|
| Catalog connection fails after previous success | Check current wallet validity, connection permissions and approved credentials. A historical wallet fix is not proof that today's connection works. |
| Native owner cannot be resolved | Set the exact physical `oracle_schema` only after verifying it through the catalog/authorized database metadata. |
| Schema/type contract fails | Compare uppercase column names, exact target types, JSON maps and timestamp handling. Use a new reviewed target or explicit migration; the helper does not silently recreate incompatible tables. |
| Source is unclustered | Expected in the reference publication. The appendix skips retrofitting clustering; publication does not require a source rebuild. |
| `DATA_ACCESS_LAYER_0068` during changed-data replacement | This remains an unverified connector path. Inspect the attempted target, compare timestamp/schema behavior, and obtain a reviewed connector/schema fix or select new target names. Do not claim a successful refresh from initial-create evidence. |
| Dry run passes; write fails | Dry run proves read/preflight only. Verify create/write grants, supported connector options and native type handling separately. |
| One target verifies; second fails | Treat publication as partial. Inspect both attempted targets; no cross-table rollback or automatic retry exists. Do not expose mismatched tables as one reconciled publication. |
| Table exists but OAC cannot see it | Refresh external-catalog metadata and wait for its Job Run; inspect discovered casing/names and OAC connection permissions. |
| Optional indexes absent | Default connector publication does not execute optional native index DDL. That route was not exercised in the reference validation. |

After a partial write, append is not a recovery strategy. Reconcile full row multisets and both target records before accepting a replacement publication.
