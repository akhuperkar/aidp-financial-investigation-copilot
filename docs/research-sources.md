# Research sources and claim boundaries

Prepared for the article dated **18 October 2026**. External sources were checked directly on that date. The article's primary-source links support industry context and product descriptions; demonstration outcomes come from the separate project evidence described below.

The machine-readable companion is [article/references.json](../article/references.json). No source is used to establish a causal result or a measured business improvement for this demonstration.

## Primary research

| ID | Source and publication date | Population and interpretation |
|---|---|---|
| GARTNER-2025-63 | [Lack of AI-Ready Data Puts AI Projects at Risk](https://www.gartner.com/en/newsroom/press-releases/2025-02-26-lack-of-ai-ready-data-puts-ai-projects-at-risk), 26 February 2025 | July 2024 survey of 1,203 data-management leaders. The 63% combines organizations lacking suitable AI data-management practices with those unsure whether they have them. It is not an AI project failure rate. |
| MCKINSEY-2025-21 | [The state of AI: How organizations are rewiring to capture value](https://www.mckinsey.com/capabilities/quantumblack/our-insights/the-state-of-ai-how-organizations-are-rewiring-to-capture-value), 12 March 2025 | The 21% concerns respondents reporting organizational gen-AI use and fundamental redesign of at least some workflows. The full survey ran 16–31 July 2024, with 1,491 participants in 101 nations; the relevant subgroup size is not separately stated in the page text. |

Both findings are dated evidence, not claims about the current October 2026 adoption rate. The article uses short paraphrases with direct links and no extended quotations. The research supports attention to data readiness and workflow design; applying that lesson to the copilot is the author's design judgment.

## Current Oracle documentation

| ID | Primary source | Supported use in the article |
|---|---|---|
| ORACLE-AIDP-OVERVIEW | [Overview of Oracle AI Data Platform](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/overview-oracle-ai-data-platform.html) | Medallion layers, Spark notebooks and ML are documented use cases. This establishes platform context, not successful execution of this project's pipeline. |
| ORACLE-AGENT-TOOLS | [About Agent Tools](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/agent-flow-tools.html) | Predefined SQL with runtime parameters, and knowledge-base retrieval. See the detailed “SQL Tool” and “RAG” sections. |
| ORACLE-EXTERNAL-CATALOGS | [External Catalogs](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/external-catalogs.html) | External metadata discovery and remote queries. Registration is distinct from this project's native-table publication and row reconciliation. |
| ORACLE-AGENTS-LANDING | [AI Agents](https://docs.oracle.com/en/cloud/paas/ai-data-platform/aidug/ai-agent-flows.html) | Navigation reference only; substantive product claims use the dedicated tools documentation. |

**Version nuance:** the agent-tools page's introductory summary says SQL uses external catalogs only. Its detailed SQL section documents both Spark SQL against standard catalog tables and Oracle SQL against external databases. The source project uses the existing Spark route. Check the actual tenant's SQL-tool controls and runtime before configuring a new deployment. Do not turn the conflicting introductory sentence into a claim that the reference implementation used AILH for all agent queries.

Oracle documentation is continuously maintained; the retrieved pages did not expose a reliable page-specific publication date. Their access date is recorded separately from the article's date.

## Project evidence

The frozen public numerical record is [data/reference-snapshot.json](../data/reference-snapshot.json). This article was written from the publication brief and inspected project sources. It did not rerun hosted Oracle services. The repository's [metrics and methodology](metrics-and-methodology.md), [architecture](architecture.md) and [hosted acceptance](hosted-acceptance.md) documents provide the operational context.

| Evidence | Article use | Boundary |
|---|---|---|
| OAC/reference Gold review, verified 17 October 2026 | 149,658 source transaction rows; 52,735 account-month rows; 5,000 accounts; 2024 coverage; December reference table and queue facts | Reference is source Delta v4. Do not substitute older agent/Streamlit totals or imply a new live check. |
| Seven SQL files in `sql/` | Describes reporting context, portfolio, queue, account and evidence tool responsibilities | Current queries use `finance.agent_demo_fs` Spark snapshot tables. They are predefined queries rather than unrestricted NL2SQL. |
| Medallion and AILH notebooks in `notebooks/` | Bronze/Silver/Gold responsibilities, separate ML exercise and native publication mechanics | Silver validates required fields; its risk-derived “data quality score” is not an independent quality measure. No production detection claim is supported. |
| Eight text documents in `rag_corpus/` | Rule thresholds, priority logic, citations and analyst guidance | Fictional policies. Score 60 is not flagged; P1 logic preserves its OR and AND conditions. |
| AILH validation record | Initial two-table native publication and full-row comparison | Changed-data replacement remains unvalidated after `DATA_ACCESS_LAYER_0068`. Optional native DDL was not executed. Preserve the unclustered source layout. |
| Agent Hub outcome and exported trace | User-reported success for seven prompts | Export contains root only; it does not prove every nested tool call. |
| Historical Streamlit acceptance record | Separates endpoint/SQL response success from answer validation | Hybrid follow-up transport succeeded but content reconciliation failed. A fresh hosted acceptance check is still required. |

### Core numerical definitions

Gross is `sum(abs(amount))`; net is `sum(amount)`; flagged gross applies the strict `risk_score > 60` filter to absolute amounts. Flag rate divides flagged transaction count by transaction count. Queue order is flagged gross descending, flagged count descending, account ID ascending. P1 is displayed separately from exposure rank. Neither flag rate nor queue rank is a calibrated fraud probability.

The December reference's top-ten share is `236847.35 / 12547752.55 × 100 = 1.8875679055%`, displayed as **1.89%**. Its flag rate is `4934 / 12699 × 100 = 38.8534530278%`, displayed as **38.85%**. Amounts retain two decimals.

## Selected writing references

The user selected two author articles: [Agent Factory walkthrough](https://medium.com/@abhijit.khuperkar/can-we-use-these-agents-in-our-own-app-a-practical-agent-factory-walkthrough-5740cd14b286) and [PII governance article](https://medium.com/@abhijit.khuperkar/from-pii-discovery-to-governed-action-with-oracle-select-ai-agent-31d1c2da8c42), with the [PII repository article directory](https://github.com/akhuperkar/pii-governance-agent/tree/main/article) as an alternative source of original prose. Those pages were not retrievable in this authoring run. The draft therefore follows the explicit tone instructions and approved outline without claiming a retrieved style match. Retrieval status provides no evidence about the articles' contents or publication availability.

## Excluded claims and outstanding evidence

- The unverified 83% claim was excluded. The unrelated 88% AI-use statistic was not used as a workflow-disconnection claim.
- No observed time saving, fraud loss reduction, calibrated probability, production precision/recall or business ROI is claimed.
- No implemented external-action tool, approval workflow or account restriction is claimed.
- Current hosted hybrid content acceptance and changed-data AILH replacement are outstanding. Initial publication success does not establish either.
- A recorded video and actual Medium/YouTube publication URLs remain pending. The article keeps `{{YOUTUBE_DEMO_URL}}` visibly unresolved.
