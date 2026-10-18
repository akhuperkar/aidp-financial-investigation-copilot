# Build and run the Financial Investigation Copilot

This guide reproduces the data contracts, analytical views and read-only investigation workflow for fictional Meridian Demo Bank. It takes you from Spark Gold tables to a supervisor with four specialist agents, then to Agent Hub and a local Streamlit client.

**Demonstration dataset; amounts shown in INR.** Screening flags and exposure rankings guide analyst review. They do not establish confirmed fraud or loss. The separate random forest training example does not supply predictions to the agent.

The hosted evidence is partial: native AILH publication and a Streamlit SQL response were verified historically; the recorded Streamlit hybrid follow-up passed transport but failed content reconciliation. Complete [hosted acceptance](hosted-acceptance.md) in your environment before presenting a fully reconciled hybrid result.

## 1. Choose a reproduction path

| Path | What you need | What it establishes |
|---|---|---|
| Local app | Python 3.10+, an approved endpoint, network access and its credentials | Streamlit UI and endpoint integration after live tests |
| Local calculations | Python, Java 17 and validation dependencies | Seeded Spark calculation checks with a local catalog/Parquet adapter |
| AIDP agent | AIDP workspace, Spark cluster, AI Compute, model access, read grants and a Knowledge Base | Actual hosted SQL, retrieval, orchestration and deployment after acceptance |
| AILH/OAC extension | Existing Gold, an external catalog connection to AILH, database privileges and OAC access | Native publication and executive analytics after reconciliation |

AILH is an additional consumer path. The supplied seven agent SQL tools query `finance.agent_demo_fs` in Spark. Creating native AILH Gold tables does not redirect those tools or create their semantic tables in Oracle.

## 2. Get the package and prepare local Python

Run commands from the repository root:

```bash
git clone https://github.com/akhuperkar/aidp-financial-investigation-copilot.git
cd aidp-financial-investigation-copilot
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements/app.txt
```

For OCI API-key or security-token authentication, install the optional SDK into the **same** environment:

```bash
pip install -r requirements/oci.txt
```

OAuth bearer authentication uses the base app dependencies. No `.env` file loader is implemented. Use environment variables, the UI or private Streamlit secrets. Keep populated secrets, keys, wallets and local history outside version control.

For local calculation validation:

```bash
pip install -r requirements/validation.txt
java -version
export AIDP_JAVA_HOME='/path/to/your/java-17-home'
python scripts/validate_notebooks.py
python -m unittest discover -s validation -p 'test_fs_ailh_notebook.py' -v
PYTHONPATH=apps/copilot python -m unittest discover -s apps/copilot/tests -v
```

Use a Python version supported by the pinned PySpark validation dependency. The validation runner uses Spark 3.5.3 and Java 17; its fixture seeds the original generator with `42`, translates three-part catalog names and substitutes Parquet for Delta. It skips source clustering DDL and ML training. It does not emulate cloud grants, AILH writes, retrieval or LLM routing. Do not import `validation/local_spark_fixture.py` into AIDP. Local outputs are rehearsal evidence, with counts distinct from the published cloud snapshot.

## 3. Prepare AIDP and run the notebooks in order

Create or select a workspace with permission to read/write the demonstration catalog and schemas. Start a compatible Spark cluster and attach it to Workbench. Separately provision or select active AI Compute for the Agent Flow. Confirm the intended OCI region, enabled model providers, quotas and execution identities before configuring nodes.

Import these notebooks without renaming them:

| Order | Notebook | Action |
|---|---|---|
| 1 | [`financial_services_medallion_architecture_demo.ipynb`](../notebooks/financial_services_medallion_architecture_demo.ipynb) | Create Bronze/Silver/Gold in a new demo environment, or reuse existing reconciled Gold |
| 2 | [`financial_services_executive_analytics_dashboards_aidp.ipynb`](../notebooks/financial_services_executive_analytics_dashboards_aidp.ipynb) | Validate the Gold contract and inspect monthly analytics |
| 3 | [`financial_services_multi_agent_demo_setup_aidp.ipynb`](../notebooks/financial_services_multi_agent_demo_setup_aidp.ipynb) | Create the agent's snapshot tables, registries and SQL smoke results |
| Optional, after 1 | [`financial_services_medallion_architecture_demo_ailh.ipynb`](../notebooks/financial_services_medallion_architecture_demo_ailh.ipynb) | Run only the appended AILH publication section against existing Gold |

The AILH notebook contains the original medallion notebook followed by an appendix. Running both complete notebooks regenerates the source twice. Existing tables are overwritten by the source pipeline; use a separate demo namespace for a fresh run. To preserve a frozen dataset, skip source generation and run the consumers against that dataset.

### 3.1 Create or inspect the medallion source

The source creates:

```text
finance.bronze.account_transactions_bronze
finance.silver.account_transactions_silver
finance.gold.transaction_analytics_gold
finance.gold.fraud_detection_model_gold
```

It generates 5,000 account identifiers with 10–50 transactions per account during 2024. The source generator has no random seed; reruns produce different counts, quantities and account rankings. A notebook's saved output is a historical result, not a guarantee for the next run. See [reproduction levels and metrics](metrics-and-methodology.md).

Inspect the persisted tables, rather than assuming that the original CREATE TABLE declarations describe every later DataFrame overwrite:

```python
spark.table("finance.gold.transaction_analytics_gold").printSchema()
spark.table("finance.gold.fraud_detection_model_gold").printSchema()
spark.sql("SELECT COUNT(*) AS rows FROM finance.gold.fraud_detection_model_gold").show()
spark.sql("DESCRIBE HISTORY finance.gold.fraud_detection_model_gold LIMIT 1").show(truncate=False)
```

The source has Spark/Delta clustering statements. Verify your runtime supports the specific statement before executing it. The reference Gold sources were unclustered; unsupported ALTER clustering was not used to rebuild them. Native AILH tables do not implement Delta liquid clustering.

The random forest cells are a separate ML workflow demonstration. You can inspect their training and evaluation after data creation; the dashboard and agent do not depend on the fitted model or its transient predictions.

### 3.2 Run executive analytics

Set these variables in the dashboard setup cell, then run from the top:

```python
CATALOG = "finance"
REPORT_MONTH = None         # latest observed; or an observed 'YYYY-MM'
ACCOUNT_IDS = []            # all; or actual ACC identifiers from your data
TREND_MONTHS = 12
TOP_N = 10
ENABLE_ENTERPRISE_LLM = False
```

Keep `ENABLE_ENTERPRISE_LLM=False` for deterministic executive wording. An optional `enterprise_llm(prompt)` callable is a separately supplied integration, not a required packaged service. An account filter applies to every chart, denominator and brief; do not label filtered numbers as enterprise totals.

The notebook checks both Gold tables at account-month grain, including category distributions. Resolve a failed reconciliation before creating the agent snapshot. A missing calendar month is a gap; it must not become zero or a substitute month.

### 3.3 Materialize the agent surface

In the multi-agent setup notebook use:

```python
CATALOG = "finance"
AGENT_SCHEMA_NAME = "agent_demo_fs"
WRITE_RAG_DOCUMENTS = False
RAG_OUTPUT_DIRECTORY = None
```

If exporting the embedded corpus to a volume, first create an authorized, notebook-accessible folder and then use:

```python
WRITE_RAG_DOCUMENTS = True
RAG_OUTPUT_DIRECTORY = "/Volumes/<catalog>/<schema>/<volume>/rag_corpus"
```

Run the notebook top-to-bottom. It validates source rows and Gold reconciliation, writes `PREPARING`, creates four physical Delta data tables, runs all seven parameterized SQL smoke queries, checks source stability, and only then writes `READY`.

```sql
SELECT snapshot_id, status, min_period_key, max_period_key,
       rule_version, currency_assumption, spark_session_timezone
FROM finance.agent_demo_fs.snapshot_metadata_sql;
```

Continue only when the single context row is `READY`. The four tables are `portfolio_monthly_sql`, `account_risk_monthly_sql`, `transaction_evidence_sql` and `exposure_mix_monthly_sql`. Preserve the printed explicit period and actual seed account for tool tests. `sql_smoke_results` records the notebook checks.

Changing `CATALOG` or `AGENT_SCHEMA_NAME` remaps the notebook registry. The separate JSON/SQL files still contain their default identifiers: use the remapped registry or update every tool configuration consistently. Rebuild this snapshot after a source refresh, with no concurrent source updates or investigations. `READY` is a publication convention, not a multi-table transaction lock.

## 4. Ingest and verify the eight policy documents

1. Upload all eight [`rag_corpus/*.txt`](../rag_corpus/) files into one managed/external volume folder. Keep unrelated and superseded policies out of that data source.
2. Compare file hashes and document IDs with [`config/rag_manifest.json`](../config/rag_manifest.json). The manifest is lineage metadata; it does not automatically create a Knowledge Base or supported retrieval filter.
3. In Master Catalog create a Knowledge Base, for example `fs_investigation_kb`, in an authorized catalog/schema. Select an available embedding model and the ingestion compute required by your tenant.
4. Add the volume folder as its TXT data source. A practical starting point is 1,500-character chunks with 200-character overlap, where the UI exposes those units. These are tunable rehearsal settings, not product defaults.
5. Start ingestion and inspect Job Runs until it succeeds. Record the embedding model, settings, corpus hash/version and ingestion completion time.
6. Create the RAG tool `retrieve_fs_investigation_policy`, select **your** successfully ingested Knowledge Base, and start with six retrieved chunks. Copy the description and preamble from [`agents/prompts/`](../agents/prompts/) and settings from [`agents/node-configurations.json`](../agents/node-configurations.json). Replace any reference KB selection with your actual object.
7. Test retrieval independently before connecting the supervisor. Inspect the actual chunks, including explicit section headers and adjacent continuation text; a synthesized tool answer alone is insufficient.

| ID | File | Purpose |
|---|---|---|
| FS-NOTICE-001 | `00_synthetic_demo_notice.txt` | Scope and interpretation |
| FS-POL-001 | `01_synthetic_transaction_triage_policy.txt` | Flag and P1 predicates |
| FS-OPS-001 | `02_analyst_investigation_playbook.txt` | Analyst review procedure |
| FS-DATA-001 | `03_medallion_data_dictionary.txt` | Field and grain definitions |
| FS-GOV-001 | `04_model_and_synthetic_risk_limitations.txt` | Score/model limitations |
| FS-EVID-001 | `05_evidence_and_citation_standard.txt` | Evidence/citation requirements |
| FS-PRIV-001 | `06_human_review_and_data_handling.txt` | Handling and review boundaries |
| FS-BRIEF-001 | `07_investigation_brief_template.txt` | Brief structure |

Version 1.0 documents carry an effective-from date of 2024-01-01 and explicit synthetic scope. Test these two narrow queries:

```text
Retrieve FS-POL-001 v1.0 section 1. Is risk_score=60 flagged?
Return the exact flag sentences and their explicit source header.

Retrieve FS-POL-001 v1.0 section 2. Return the complete P1 account-month
rule, both alternatives, all score and amount conditions, and any adjacent
chunk continuation. Preserve AND/OR and inclusive/exclusive comparisons.
```

Accept only actual passages showing `risk_score > 60`, and P1 when flagged gross is at least INR 10,000 **or** at least one transaction has score at least 85 **and** absolute amount at least INR 5,000. Cite `[FS-POL-001 v1.0 §1]` and `[FS-POL-001 v1.0 §2]` only when the returned headers support them. Chunk indices are not section numbers.

For a policy revision, create a new explicit document version/effective scope, update the manifest, remove superseded material from the selected data source as your ingestion mechanism requires, reingest and rerun retrieval tests. Never assume uploading a replacement immediately removes old vector chunks. If SQL rule metadata and retrieved policy disagree, withhold the policy conclusion and resolve the version mismatch.

## 5. Configure all seven SQL tools

The source of truth is [`config/sql_tools.json`](../config/sql_tools.json), with readable templates under [`sql/`](../sql/). These are predefined read queries with numeric substitutions; the agent does not generate arbitrary SQL.

The reference route selects **Spark SQL**, catalog `finance`, schema `agent_demo_fs`, and a running Spark cluster. Oracle's current [detailed SQL tool section](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/agent-flow-tools.html) describes Spark and Oracle dialects, although the same page's overview still says external-catalog only. Verify the dialect and catalog selectors in your tenant and run a direct tool test. If only Oracle SQL is available, port and validate the semantic surface and syntax explicitly; changing the catalog selector alone cannot run these Spark templates against the two native Gold tables.

For each tool, add a SQL node to the indicated executor; copy its name, description, `configuration` object and parameter definitions from the JSON; choose Spark SQL and your cluster; set the row cap; Apply; then use Test with your actual resolved period/account. Example static configuration:

```json
{
  "catalogKey": "finance",
  "schemaKey": "agent_demo_fs",
  "query": "SELECT * FROM finance.agent_demo_fs.snapshot_metadata_sql WHERE status = 'READY' LIMIT 1",
  "isRowLimitEnabled": true,
  "maxRows": 1
}
```

| Tool | Executor | Parameters | Cap | Result |
|---|---|---|---:|---|
| `get_reporting_context` | PORTFOLIO_SQL_AGENT | none | 1 | READY scope, snapshot, rule and coverage |
| `get_portfolio_snapshot` | PORTFOLIO_SQL_AGENT | `period_key` | 1 | Complete monthly portfolio totals |
| `get_portfolio_trend` | PORTFOLIO_SQL_AGENT | `period_key` | 12 | Latest observed months ending at the requested month |
| `get_exposure_mix` | PORTFOLIO_SQL_AGENT | `period_key`, `dimension_code` | 30 | One type/location breakdown |
| `get_priority_accounts` | INVESTIGATION_SQL_AGENT | `period_key` | 10 | Exposure-ranked flagged accounts and total candidates |
| `get_account_snapshot` | INVESTIGATION_SQL_AGENT | `period_key`, `account_number` | 1 | Complete selected account-month totals |
| `get_account_transaction_evidence` | INVESTIGATION_SQL_AGENT | `period_key`, `account_number` | 20 | Source-content groups with duplicate multiplicity |

| Parameter | Type/default | Contract |
|---|---|---|
| `period_key` | number, `0` | Integer YYYYMM; 0 resolves latest once, then reuse the returned explicit period; intended bounds 0–999912 |
| `dimension_code` | number, `1` | Integer 1 = transaction type; 2 = location label; never combine the two dimensions |
| `account_number` | number, `1` | Integer suffix, bounds 1–99999999; `ACC00000001` maps to 1; use an account actually returned by the queue |

Defaults do not prove a particular account exists in your selected period. A numeric UI type may not enforce integer bounds: test strings, SQL fragments, decimals, booleans and out-of-range values in the hosted Test interface. The local validator enforces bounded integers only in its own smoke tests. Stop hosted rollout if inputs can escape this contract; retain a SELECT-only execution identity.

Test `get_reporting_context` first; `get_portfolio_snapshot(period_key=0)` next; then reuse its explicit period for the other tools. A valid missing month, such as `202606` for this 2024 dataset, must return no rows. Compare every result's `snapshot_id` to the READY context.

## 6. Build the supervisor and four specialists

Create a visual flow named `FS_Investigation_Copilot` and attach active AI Compute. Add `Message → Guardrails → FS_INVESTIGATION_SUPERVISOR`. Connect four executors to the supervisor as delegated specialists; these connections are not a serial data pipeline. Prefer stateless executor isolation and pass scope/evidence explicitly.

Use the current [`agents/node-configurations.json`](../agents/node-configurations.json) and matching individual texts in [`agents/prompts/`](../agents/prompts/). Older notebook-embedded `PROMPTS`, `config/prompts.json` and archived HTML are historical scaffolding; they can differ in output format and the briefing parameter name.

| Node | Reference model selection | Output tokens | Temperature | Attached tools |
|---|---|---:|---|---|
| FS_INVESTIGATION_SUPERVISOR | `xai.grok-4.7` | Provider-controlled | Provider-controlled | Four executors |
| PORTFOLIO_SQL_AGENT | `google.gemini-2.5-flash-lite` | 2048 | 0 | Four portfolio SQL tools |
| INVESTIGATION_SQL_AGENT | `google.gemini-2.5-flash` | 4096 | 0 | Three account SQL tools |
| POLICY_RAG_AGENT | `google.gemini-2.5-flash` | 3072 | 0 | `retrieve_fs_investigation_policy` |
| INVESTIGATION_BRIEF_AGENT | `google.gemini-2.5-flash` | 4096 | 0 | `compose_investigation_brief` |
| RAG tool | `cohere.command-a-03-2025` | 2500 | 0 | Your ingested Knowledge Base; six chunks |
| Prompt tool | `google.gemini-2.5-pro` | 8192 | 0 | String parameter `evidence_packet` |

These are recorded reference choices, not availability promises. Select supported models in your region, record substitutions, and rerun acceptance. The reference supervisor UI did not allow token/temperature configuration for its selected model; leave unavailable controls provider-managed. The RAG generation model is separate from the KB embedding model; `retrieval_limit=6` is separate from a provider's model top-k.

Configure available PII, prompt-injection and moderation controls in the Guardrails UI. Test that a legitimate synthetic ACC identifier and financial question are allowed. The guardrails note is configuration guidance, not an executable custom policy. The flow has no HTTP/MCP action tools. Prompts and a human-review footer do not implement an approval workflow.

Create `compose_investigation_brief` as a Prompt tool with the current template. Its variable must be exactly:

```text
{{evidence_packet}}
```

Define `evidence_packet` as **String**. The supervisor passes compact factual scope, selected exact SQL values, actual evidence rows, actual policy excerpts/citations and error/gap status. Keep the packet under the current supervisor's approximately 3,000-character target and task instructions under 1,200 characters, excluding factual evidence. Do not put an instruction-laden draft inside the evidence parameter. The brief executor copies the packet unchanged, invokes this tool once and returns its Markdown unchanged. A Prompt rejection is an incomplete brief; do not bypass it by obfuscating evidence or weakening guardrails.

For a full investigation, obtain context/portfolio first, resolve one explicit period, collect queue/account/evidence, make two targeted policy calls, then call the briefing gateway. The configured budget is at most eight SQL calls and two RAG calls. A simple portfolio question should not invoke every specialist. Inspect traces for actual tool inputs/results, not presumed private reasoning.

## 7. Test, create the card and deploy

Run individual tool tests before the integrated flow. Then run all cases in [`config/acceptance_cases.json`](../config/acceptance_cases.json) and record dated results in [`config/tenant_acceptance_log.csv`](../config/tenant_acceptance_log.csv). The seven presenter prompts are a useful rehearsal subset; they are not the complete negative/control suite. Follow the [hosted acceptance worksheet](hosted-acceptance.md) for exact gates.

Create the Agent Card from [`agent_card/agent-card.editable-metadata.json`](../agent_card/agent-card.editable-metadata.json) and [`agent_card/agent-card.form-fields.txt`](../agent_card/agent-card.form-fields.txt). Use the four skills: Portfolio Risk Analytics; Account Triage and Transaction Evidence; Synthetic Policy Retrieval; Grounded Investigation Brief. Agent version `1.0.0` is separate from A2A protocol `0.3.0`. Keep generated transport/input/output fields under AIDP control. Set documentation/provider URLs only to real published resources owned by the actual operator. Fictional Meridian Demo Bank is not the service owner.

In your tenant's deployment workflow:

1. Select the intended **deployment** AI Compute and deployment-approved authorization. Playground attachment is a separate setting.
2. Deploy the reviewed flow and retrieve the actual published endpoint/card from Details. Changes require redeployment. Follow Oracle's [deployment guide](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/agent-flow-deployment.html) for your version.
3. Register/select the deployed AIDP agent in AI Registry with the actual endpoint/card fields that its UI requests. A draft card with an empty URL is not a deployable published card.
4. Select that registry entry in Agent Hub. Test a small capability question, a focused SQL request, a policy request, the full hybrid brief and a same-account follow-up. Confirm the final response appears in Hub and reconcile it with the raw evidence.
5. Keep both the hosting AI Compute and the Spark SQL dependency available for the session. Deployment status, registry presence and card access each establish less than successful end-to-end invocation.

## 8. Run the dual-provider Streamlit app on port 8501

From the repository root, using the same activated environment:

```bash
python -m streamlit run apps/copilot/app.py --server.port 8501 --server.address 127.0.0.1
```

Open [localhost:8501](http://localhost:8501). The Python process needs network access to the selected provider. It makes the requests; the browser does not connect directly to the agent endpoint.

To load the bundled `.streamlit/config.toml` theme and app-local secrets, launch with `apps/copilot` as the working directory instead:

```bash
cd apps/copilot
python -m streamlit run app.py --server.port 8501 --server.address 127.0.0.1
```

This keeps the same active venv and port. Return to the repository root before running the other repository commands. Streamlit secrets are resolved from its configured secrets locations; placing a populated file in a directory that is not loaded will not configure the app.

### AIDP settings and first request

The following names are implemented by the app. Replace placeholders locally; do not commit credential values:

```bash
export COPILOT_CUSTOMER_NAME='Meridian Demo Bank'
export AIDP_ENDPOINT='https://aidp.example.com/agentendpoint/<deployment-id>/a2a'
export AIDP_AUTH='OCI API key profile'
export AIDP_OCI_PROFILE='YOUR_APPROVED_PROFILE'
export AIDP_OCI_CONFIG="$HOME/.oci/config"
export AIDP_TIMEOUT='600'
# Optional title override; leave empty to follow customer branding.
export AIDP_DISPLAY_NAME=''
```

Use the endpoint actually published by your deployment; the example domain is a placeholder. An existing Chat or Agent Card URL is normalized to its corresponding A2A URL. Select **Oracle AIDP** in **Agent provider**, check the settings, then click **Connect / verify AIDP**.

For security-token profiles use `AIDP_AUTH='OCI security-token profile'`; the selected OCI config needs a valid security token file and matching key. For an OAuth deployment choose `AIDP_AUTH='OAuth bearer token'` and enter the issued bearer token in the masked UI field (or private `AIDP_BEARER_TOKEN`). `AIDP_DH_USER_PRINCIPAL` is optional and only appropriate when required by the deployment gateway. Do not invent it or reuse a PAF cookie. `AIDP_CA_BUNDLE` can point to an approved CA file; external TLS verification stays enabled.

Connect verifies the published card's URL, A2A `0.3.0` version and JSON-RPC transport. Send a request to establish invocation permission:

```text
What can you help with? Reply in three bullets without querying data.
```

Then test portfolio SQL and the full hybrid prompt from the acceptance catalog. Inspect Raw response and evidence references. A completed protocol task alone does not establish a correct answer.

### PAF settings and independent transport

Choose **Private Agent Factory**, then **External server** or **Local MacBook**. Example public-safe variable names:

```bash
export PAF_ORIGIN='https://paf.example.com'
export PAF_AGENT_ID='<agent-id-from-your-installation>'
export PAF_ROOM_PATH='roomId'
export PAF_DISPLAY_NAME=''
```

Use the installation's supported API key, username/app-password or session-cookie mode. API-key routes use `/agentFactory/v1/integrations/agents/<agent-id>/run`; older cookie routes depend on the selected agent type and build. Use **Full endpoint override** / `PAF_ENDPOINT` for an actual copied route. Additional implemented mappings are `PAF_CA_BUNDLE`, `PAF_ANSWER_PATH`, `PAF_ROWS_PATH` and `PAF_SOURCES_PATH`. Local defaults use the equivalent `PAF_LOCAL_*` prefix. Enter passwords and cookies in masked fields.

PAF REST uses `roomId`; AIDP uses A2A `message/send`, `tasks/get` and `contextId`, with task resumption only when input is required. They share the UI, response views and local history utility; they do not share credentials, request schemas or conversation IDs. Adding AIDP does not deploy this financial workflow into PAF. A PAF selection calls whichever agent you configure there.

### Branding, response views and history

Under either provider's settings, open **Customer branding**, edit **Customer name** and click **Apply**. It updates the heading below the Oracle wordmark and the default title. **Reset**, or a blank applied name, uses `Demo Customer`. Default titles are `<Customer> AIDP Agent Copilot` and `<Customer> Agent Factory Copilot`. A nonempty **Assistant title** overrides the generated title after connection settings are applied. Keep it blank for customer edits to control the title. Branding changes do not change endpoint, identity or history scope.

Markdown and citations are displayed as returned. Table/Visualization views need actual structured rows; the UI does not invent chart data from prose. AIDP cards may advertise streaming, but this client presents the response after synchronous completion/polling rather than rendering a token stream.

Local history is stored separately for PAF and AIDP, scoped to endpoint and authorization identity. `PAF_HISTORY_DB` and `AIDP_HISTORY_DB` override their SQLite paths. **New chat** clears active remote-context references; switching provider/profile disconnects. Deleting local turns does not delete provider-side history or durable memory. The local app is a presenter client; multiuser hosting needs a deliberate application identity and access design.

## 9. Optional AILH publication and OAC

Use the AILH notebook's appended section only—zero-based cells 29–40, displayed as cells 30–41. Keep the original 29 cells untouched when preserving existing Gold.

1. Configure `AILH_CONNECTION` with your existing external catalog/schema and, if needed, the exact physical Oracle owner. Configure `AILH_TARGET_TABLES` for the two native destination names.
2. Set `AILH_PUBLICATION["enabled"]=True`, retain `dry_run=True`, `verify_full_rows=True`, `optimize_source_gold=False` and `AILH_NATIVE_DDL["execute"]=False`. Run the appendix top-to-bottom.
3. Inspect pinned source Delta versions, schemas, counts, existing target compatibility and resolved owner. Dry run validates reads/preflight; it does not validate writer privileges or connector replacement behavior.
4. For initial publication, set `dry_run=False` and rerun the appendix. Require `status="verified"` and **two** verified target records with full-row comparison. Use `existing_table_action="create_only"` with unused names if you want to refuse existing targets.
5. Refresh external-catalog metadata, wait for its Job Run, and inspect the native tables through the catalog. Point your OAC dataset at that verified native publication and reconcile the selected month with the [methodology reference](metrics-and-methodology.md).

The connection uses catalog-managed credentials. Optional direct DDL uses `FS_AILH_DSN`, `FS_AILH_USER`, `FS_AILH_PASSWORD`, `FS_AILH_TNS_ADMIN`, `FS_AILH_WALLET_DIR` and `FS_AILH_WALLET_PASSWORD` only when explicitly enabled. It needs `python-oracledb`, correct native privileges and an extracted wallet directory if using mTLS. This optional DDL/index route was **not executed** in the reference validation.

Initial two-table publication and unchanged-data verification succeeded historically. Changed-data replacement is **unverified** and can fail `DATA_ACCESS_LAYER_0068`; it is not a proven idempotent refresh path. Inspect attempted targets after failure. Do not append duplicates or assume cross-table rollback. Source Delta layout and native Oracle indexes are separate concerns. See [troubleshooting](troubleshooting.md) before a refresh.

### Rebuild the OAC workbook

The screenshots document an OAC workbook; they are not an importable workbook export. Recreate the analytical content using the native publication and Oracle SQL below. The complete [six-canvas OAC recipe](oac-workbook.md) supplies exact measures, formats, filter scopes and the shared Auto Fit/header layout. Styling and control placement can vary with OAC versions.

1. Create or select an approved OAC connection to the AILH database, using a read-only identity that can select the two published native Gold tables. Validate that the connection reaches the same native publication you reconciled.
2. Create an account-month SQL dataset from [`sql/oac/account_month_risk.sql`](../sql/oac/account_month_risk.sql). Replace `GOLD` with your verified physical owner if different. This query derives exact account totals and screening priority from transaction Gold, then adds the monthly exposure rank and monthly flagged-gross denominator.
3. Create a monthly SQL dataset from [`sql/oac/monthly_risk_review.sql`](../sql/oac/monthly_risk_review.sql), with the same owner substitution. It returns portfolio totals, P1 count, top-ten concentration and calendar-aware prior-month changes. Create a separate transaction-level dataset from the native `FRAUD_DETECTION_MODEL_GOLD` for type/location breakdowns. Do not join complete monthly totals onto raw transaction rows and then sum them.
4. Set account IDs, report month, type, location and priority as attributes. Treat counts/amounts as measures; keep precomputed percentage/rank fields from being summed. Restrict a KPI to one monthly row. Use `100 * SUM(RULE_FLAGS) / SUM(TRANSACTION_COUNT)` for a count-based rate across an explicitly selected population, rather than averaging account percentages.
5. Create the six canvases below. Use a consistent selected month, INR formatting with two decimal places, integer counts and percentages with one or two decimal places. Keep `REPORT_MONTH` in the trend dataset so a single-month canvas filter does not unintentionally remove its full history.

| Canvas | Dataset and content |
|---|---|
| Executive Snapshot | One monthly row: transactions, active accounts, gross/net activity, rule flags, flagged gross, flag rate and P1 count |
| Executive Brief | Fixed December reference narrative, visibly labeled and excluded from dynamic filter claims |
| Activity and Risk Trends | Monthly rows: transaction/gross/flagged-gross time series; disclose missing calendar months |
| Investigation Queue | Account-month rows with `RULE_FLAGS > 0`, ordered by `EXPOSURE_RANK`; show first ten accounts and complete account metrics |
| Monthly Changes | Monthly rows with adjacent-calendar-month changes; show rate changes in percentage points |
| Risk Exposure | Transaction type or location-label aggregation, one dimension at a time; gross/flagged gross and count-based rate |

For a transaction-level breakdown, the underlying Oracle SQL pattern is:

```sql
SELECT TO_CHAR(TRANSACTION_DATE, 'YYYY-MM') AS REPORT_MONTH,
       TRANSACTION_TYPE,
       COUNT(*) AS TRANSACTIONS,
       SUM(ABS(AMOUNT)) AS GROSS_ACTIVITY_INR,
       SUM(CASE WHEN RISK_SCORE > 60 THEN 1 ELSE 0 END) AS RULE_FLAGS,
       SUM(CASE WHEN RISK_SCORE > 60 THEN ABS(AMOUNT) ELSE 0 END) AS FLAGGED_GROSS_INR,
       100.0 * SUM(CASE WHEN RISK_SCORE > 60 THEN 1 ELSE 0 END)
             / NULLIF(COUNT(*), 0) AS FLAG_RATE_PCT
FROM GOLD.FRAUD_DETECTION_MODEL_GOLD
GROUP BY TO_CHAR(TRANSACTION_DATE, 'YYYY-MM'), TRANSACTION_TYPE
```

Replace `TRANSACTION_TYPE` with `LOCATION` for the separate location view. Do not add both breakdown totals together. Native transaction types/locations remain source labels.

6. Validate a selected month against direct native SQL and the same Gold version. The frozen December reference is in [`data/reference-snapshot.json`](../data/reference-snapshot.json); new generated sources must reconcile to their own outputs instead of being forced to match it. Check the top account, top-ten flagged-gross sum/share and complete P1 predicate as well as headline totals.
7. Test filters. The supplied SQL computes portfolio-wide monthly ranks/denominators before interactive account filtering. Label that scope explicitly; to calculate concentration within a filtered population, recompute ranking and denominator over that population in a separate validated query. Account filters must not leave mismatched numerator/denominator scopes.

Use the reference screenshots as a visual guide: [snapshot](../media/screenshots/executive-snapshot.png), [trends](../media/screenshots/activity-risk-trends.png), [queue](../media/screenshots/investigation-queue.png), [monthly changes](../media/screenshots/monthly-changes.png) and [exposure](../media/screenshots/risk-exposure.png). The [methodology](metrics-and-methodology.md) defines the formulas and limits.

Next: [architecture](architecture.md), [OAC workbook](oac-workbook.md), [metrics and methodology](metrics-and-methodology.md), [hosted acceptance](hosted-acceptance.md), [publication checklist](publication-checklist.md).
