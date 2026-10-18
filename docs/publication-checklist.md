# Publication and demonstration checklist

This checklist separates a reviewable public package from a currently validated hosted deployment. Check a box only after inspecting evidence; unchecked items remain pending.

## Package and provenance

- [ ] Confirm author, date, project title and fictional Meridian Demo Bank context across README, article, diagrams, app and video material.
- [ ] Preserve the four exact notebook filenames and a usable source archive under `reference/`; document sanitized/revised copies separately from original-byte hashes.
- [ ] Validate current file manifests against the packaged bytes. Do not reuse a historical manifest as the current release checksum list.
- [ ] Keep seven SQL templates, configuration dictionaries, eight corpus files, current node settings and current prompts consistent. The latest briefing variable is `evidence_packet`, String.
- [ ] Treat notebook-embedded prompts, older `config/prompts.json` and archived HTML as historical scaffolding where they differ from `agents/node-configurations.json` and `agents/prompts/`.
- [ ] Run notebook JSON/compilation checks, the relevant AILH contract tests and app tests. Run local Spark calculation validation where its required environment is available; report skipped checks explicitly.
- [ ] Test the documented venv install and app launch paths: `requirements/app.txt`, optional `requirements/oci.txt`, `requirements/validation.txt`, and `apps/copilot/app.py` on port 8501.
- [ ] Check relative links and image paths in Markdown/HTML, asset dimensions and exported rendering. Confirm local paths do not leak into published content.
- [ ] Rebuild/review the [six-canvas OAC recipe](oac-workbook.md) against both Oracle SQL datasets; preserve Auto Fit, Screen dimensions, 28/16/12 px header hierarchy and 160 × 21 px wordmark. Distinguish the fixed reference brief from filter-responsive measures.

## Claim and number review

- [ ] Place “Demonstration dataset; amounts shown in INR” near the first numerical results.
- [ ] Keep the 17 October Gold/OAC snapshot separate from earlier deployed-agent/Streamlit evidence. Match source versions, account/month, filters, rule, timezone and consumer path before comparing figures.
- [ ] Preserve gross versus net, count flag rate versus monetary concentration, account totals versus capped evidence, and queue rank versus P1 assignment.
- [ ] Explain that the unseeded source generator cannot reproduce exact frozen counts on demand. Label seed-42 local fixtures separately from cloud evidence.
- [ ] Describe random scores, threshold-derived labels and absent persisted ML predictions accurately. Do not claim that the random forest supplies the agent queue or proves production detection effectiveness.
- [ ] Keep screening versus confirmed fraud/loss distinctions near conclusions. Do not claim savings, recovered funds, balances or calibrated probabilities.
- [ ] Describe policies as fictional. Human-review language does not establish an implemented approval workflow or any external action.
- [ ] Cite external statistics to their original sources with correct population, date and wording; use [`research-sources.md`](research-sources.md).

## Architecture and operational accuracy

- [ ] Show Spark medallion Delta, the separate AILH native-publication/OAC path, and the agent's `finance.agent_demo_fs` Spark surface accurately.
- [ ] Confirm the tenant's actual SQL dialect and compute dependencies. The current detailed Oracle tool documentation covers both Spark and Oracle routes; the supplied templates target Spark.
- [ ] Do not label native AILH tables as Delta liquid-clustered. The reference sources were unclustered and retained that layout.
- [ ] State initial native publication/full-row verification separately from unverified changed-data replacement and unexecuted optional DDL/indexes.
- [ ] Explain that Playground attachment, deployed hosting compute, card/Registry registration and final Hub invocation are different checkpoints.
- [ ] Document region/model substitutions and rerun evidence. Reference model IDs are not availability guarantees.
- [ ] Verify KB ingestion completion, corpus hashes/version, full policy clauses and supported section citations; no invented chunk IDs or retrieval scores.
- [ ] Keep AIDP A2A and PAF REST credentials, session identifiers and acceptance results separate within the shared UI.

## Public-file privacy and security review

- [ ] Scan notebooks, saved outputs, Markdown, JSON, HTML, SVG, PNG screenshots, video frames/audio, file metadata and archives for private paths, real endpoints/hostnames, deployment IDs, user/session/task IDs and customer-specific data.
- [ ] Inspect recursively inside source archives. Original source hashes do not authorize publishing credentials or private runtime identifiers; retain unsafe originals privately and publish a documented sanitized archive where necessary.
- [ ] Use generic placeholders for endpoint/agent/identity examples; retain only public documentation URLs and intentional public repository/article/video URLs.
- [ ] Exclude populated Streamlit secrets, `.env`, OCI keys/config credentials, wallets, cookies, tokens, SQLite histories, raw sessions and source recordings from Git. Check staged files as well as `.gitignore`.
- [ ] Inspect app defaults, secrets examples, README examples, tests and historical verification JSON for hardcoded real endpoint/agent IDs. Sanitizing only the visible UI is insufficient.
- [ ] Keep external TLS verification and SELECT-only runtime permissions. Do not publish a hosted parameter-validation success without actually exercising that path.
- [ ] Review the repository's license and third-party asset/trademark attribution. Oracle-style colors/wordmarks do not imply Oracle authorship or certification of this example.

## Hosted evidence and readiness

- [ ] Preserve the public status ledger in [`hosted-acceptance.md`](hosted-acceptance.md): SQL UI/transport success and hybrid content failure are different outcomes.
- [ ] Keep root cause of the historical contradictory transaction rows unverified until tool/handoff/Prompt/final-output comparison establishes it.
- [ ] Run the full T01–T12 suite and record dated evidence in `config/tenant_acceptance_log.csv`. Seven presenter prompts are not the full suite.
- [ ] Reconcile direct SQL and actual policy chunks against the full hybrid answer and same-account follow-up, using one stable snapshot.
- [ ] Confirm final responses in the actual advertised entry points: Playground, Agent Hub and Streamlit. A root-only trace export cannot verify inner calls.
- [ ] Do not relabel historical `NOT_RUN`, failed or blocked cases as pass based on a screenshot, successful card read or fluent narrative.

## Article, video and release links

- [ ] Read the article beside the README, user guide and methodology; remove inconsistent figures, stale parameter names and unsupported all-pass claims.
- [ ] Review screenshots for readable labels, selected month/filter scope, consistent INR formatting and sanitized runtime identifiers.
- [ ] Record only the demonstrated path. If showing a saved/historical response or a local fixture, label it accordingly; do not present it as a new live success.
- [ ] Until video publication, keep `{{YOUTUBE_DEMO_URL}}` explicitly pending. Until article publication, keep `{{MEDIUM_ARTICLE_URL}}` explicitly pending in the README. Do not invent a watch/article URL.
- [ ] Before adding the final master, verify it exists and was reviewed; intended path is `video/final/aidp-financial-investigation-copilot.mp4`. Track the master with Git LFS and keep `video/source/` ignored.
- [ ] Check that no empty/fake MP4 or placeholder screenshot is represented as a completed recording.
- [ ] Review the final staged diff and release artifacts, then perform only the separately authorized GitHub/article/video publication actions. Package readiness does not itself authorize publishing to a service.

Companion guides: [build and run](user-guide.md), [OAC workbook](oac-workbook.md), [architecture](architecture.md), [metrics](metrics-and-methodology.md), [troubleshooting](troubleshooting.md), [hosted acceptance](hosted-acceptance.md).
