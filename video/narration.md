# Draft narration — financial investigation copilot

**Status:** production draft; no voice track or footage has been generated. Timing and chapter markers are provisional until the final edit.

**Spoken draft:** 1,845 words. At 140–150 words per minute, approximately 12.3–13.2 minutes of speech; the planned 69 seconds of silent proof holds bring the draft target to **13:59** at 145 words per minute.

**Voice:** clear adult female English voice; neutral Indian or internationally clear English pronunciation, moderate pace, calm delivery. Read ordinary prose naturally; keep technical identifiers legible in captions instead of rushing through their punctuation. No voice impersonation. Target 145 words per minute, with brief pauses after a definition or source boundary.

**Recording branches:** chapter 11 is the safe default and explicitly explains the open hybrid acceptance gate. Do not rewrite that chapter as a successful hybrid demonstration until a fresh hosted run passes the checks in `recording-guide.md` and `../docs/hosted-acceptance.md`. A limitation-led cut remains truthful but must retain the gate in both the video and description.

**Read only the blockquotes.** Headings, timing notes, and holds are production directions. Pronunciations: AIDP = “A I D P”; AILH = “AI Lakehouse” after first use; OAC = “Oracle Analytics”; SQL = “sequel”; RAG = “rag”; USD = “Indian rupees”; P1 = “P one”; A2A = “A two A”. The OAC account identifier is `ACC00004535`; show it exactly on screen. Spoken expansions increase actual duration slightly, so measure the recorded voice.

## 00-cover — Financial investigation, with evidence

Draft start 00:00 · target 18 seconds · 29 words · 6 seconds total silent proof hold within this chapter.

> Which accounts should an analyst investigate first, what evidence supports that priority, and which policy applies? This walkthrough follows that decision from the data foundation to the analyst workspace.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 01-context — Start with the analyst’s decision

Draft start 00:18 · target 67 seconds · 143 words · 7 seconds total silent proof hold within this chapter.

> At Meridian Demo Bank, an analyst needs a defensible starting point for review. A dashboard can show portfolio activity, but the investigation also needs account-level evidence and the rule that explains the priority. Finding those pieces separately creates repeated searching, copying, and reconciliation.
> The aim here is to bring the relevant information into a readable investigation brief while preserving its source and scope. The background work prepares transaction data, reporting measures, an agent query surface, and a small policy library. The foreground experience helps the analyst ask focused questions and inspect the response.
> This is a demonstration dataset, with amounts shown in Indian rupees. A screening flag is a reason to investigate; it is not a confirmed fraud finding. No external action is executed. We will first establish the evidence, then show how the agent and application make that evidence easier to use.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 02-bronze — Bronze

Draft start 01:25 · target 49 seconds · 108 words · 4 seconds total silent proof hold within this chapter.

> The first requirement is a source record that can be inspected. In the Bronze layer, the notebook creates the transaction table within the finance catalog. The fields include an account identifier, transaction date and type, signed amount, and a demonstration risk score.
> For this recording, we inspect the existing data rather than regenerate it. That matters because later totals must refer to the same recorded snapshot. The account identifier keeps its leading zeros, and the amount keeps its sign.
> Bronze gives the investigation a place to return when a summary needs explanation. It does not, by itself, establish that a transaction is suspicious or that a loss occurred.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 03-silver — Silver

Draft start 02:14 · target 50 seconds · 109 words · 4 seconds total silent proof hold within this chapter.

> Silver makes the source more usable for downstream work. The notebook applies its validation and enrichment logic, including the fields used to describe data quality and transaction timing. We inspect that logic alongside the resulting schema and a bounded sample.
> The useful question is whether the transformation preserves the meaning of the record. Account identity, timestamps, and signed amounts must remain traceable as derived fields are added.
> A clean schema is not a guarantee that every business fact is available. This dataset does not supply customer identity checks, account balances, counterparties, or confirmed fraud outcomes. The later investigation must report those gaps instead of filling them with plausible details.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 04-gold — Gold

Draft start 03:04 · target 55 seconds · 120 words · 5 seconds total silent proof hold within this chapter.

> Gold prepares two different surfaces: account-month analytics and transaction-level, machine-learning-ready data. The distinction matters. One row in an account-month table is not one transaction, and the two row counts should never be compared as if their grain were identical.
> The verified reference contains one hundred forty-nine thousand, six hundred fifty-eight source transaction rows and fifty-two thousand, seven hundred thirty-five account-month analytics rows, spanning five thousand accounts during twenty twenty-four.
> We also make the financial definitions explicit. Gross activity sums absolute amounts. Net activity preserves the signs. Flagged gross sums the absolute amounts of rule-flagged transactions, while flag rate is based on transaction counts. These definitions give the analyst a consistent way to read the queue and compare its supporting evidence.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 05-ml — Machine learning

Draft start 03:59 · target 65 seconds · 145 words · 5 seconds total silent proof hold within this chapter.

> The same foundation also supports a separate machine learning workflow. Here the notebook assembles transaction features, splits the data, trains a random forest, and evaluates predictions on the held-out partition. This shows how a training and evaluation pipeline fits into the platform.
> There is a critical limitation. The source score was generated randomly, and the training label called is fraud is defined by whether that score is strictly greater than sixty. The model does not use the score as an input feature, but its evaluation still measures agreement with this demonstration label. It does not establish performance against verified fraud outcomes.
> The deployed investigation agent does not consume these model predictions. Its queue uses deterministic screening rules from a separate prepared snapshot. We therefore treat model training as an enablement workflow, and we make no claim about learned production detection, prevented loss, or realized savings.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 06-ailh — AI Lakehouse publication

Draft start 05:04 · target 67 seconds · 149 words · 5 seconds total silent proof hold within this chapter.

> Next, the AI Lakehouse publication path makes the two Gold tables available as native Oracle tables through the existing external catalog connection. This is the path used by the Oracle Analytics view in this walkthrough.
> The important evidence is the publication check. The notebook pins the source versions, checks the target schema, and compares the published rows with the source, including duplicate multiplicity after type normalization. Row counts and decimal totals provide additional checks.
> The recorded reference verifies the initial two-table publication. It does not establish that a changed-data replacement will always succeed. That path has an unresolved connector error and needs separate validation. Optional native DDL was not executed. The source tables also remained unclustered; the native tables should not be described as implementing Delta liquid clustering.
> The result we rely on is a verified analytical publication with an explicit boundary, not a promise about every refresh operation.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 07-notebook-oac — Notebook and Oracle Analytics

Draft start 06:11 · target 90 seconds · 202 words · 6 seconds total silent proof hold within this chapter.

> The executive analytics notebook and Oracle Analytics now answer the portfolio question before we ask the agent to explain an account. We set December twenty twenty-four and keep that reporting scope visible while moving from the executive snapshot to the investigation queue.
> In the verified Oracle Analytics reference, December contains twelve thousand, six hundred ninety-nine transactions across four thousand, four hundred thirty-six active accounts. Gross activity is approximately thirty-one point six four million rupees. The rule-flag rate is thirty-eight point eight five percent. These are screening measures from this demonstration dataset, not estimates of confirmed fraud loss.
> The queue ranks accounts using the defined flagged-gross measure. In this reference, account A C C zero zero zero zero four five three five has flagged gross of twenty-eight thousand, eight rupees and three paise. We can inspect that account's supporting records rather than infer its story from the rank alone.
> There is also an important source boundary. Oracle Analytics reads the verified Gold publication. The existing agent tools read their own dedicated snapshot. When we switch to the agent, its reported snapshot becomes the authority for that conversation. We do not carry these Oracle Analytics totals into a response from the older agent snapshot.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 08-agent-builder — Agent Builder

Draft start 07:41 · target 91 seconds · 204 words · 6 seconds total silent proof hold within this chapter.

> The agent flow connects a business question with the appropriate evidence source. Its supervisor routes portfolio questions to a portfolio SQL agent, account and transaction questions to an investigation SQL agent, and policy questions to a retrieval agent. A brief-composition step formats the evidence for the analyst.
> The SQL surface contains seven predefined, parameterized tools. They retrieve reporting context, portfolio snapshots, trends, exposure mix, the priority queue, an account snapshot, and transaction evidence. This is a bounded query interface, rather than permission for the model to invent and execute arbitrary SQL.
> The retrieval side uses eight fictional policy and definition documents. The analyst can ask for a specific rule and inspect its document version and section. A complete policy clause matters more than a fluent summary of part of it.
> The model adds value by interpreting the request, retrieving relevant policy, and organizing the evidence into a readable explanation. The agent flow adds value by routing work, preserving the chosen period and account, and keeping structured results and policy context together.
> It does not freeze an account, contact a customer, create a case, or submit a filing. Human review remains a step in the analyst's work; this flow does not implement an approval workflow.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 09-testing-deployment — Testing and deployment

Draft start 09:12 · target 74 seconds · 166 words · 5 seconds total silent proof hold within this chapter.

> Before presenting a combined investigation, we test the pieces separately. First, a portfolio request must return the requested period, source snapshot, and exact SQL fields. Next, the queue and selected account must agree on the same named amounts. Transaction evidence must identify its sample limits and duplicate multiplicity.
> The policy boundary test asks whether a score of sixty is flagged. It is not: the rule is strictly greater than sixty. P one priority applies when flagged gross is at least ten thousand rupees, or when a transaction has both a score of at least eighty-five and an absolute amount of at least five thousand rupees.
> A missing-data test should withhold unavailable balances, probabilities, and confirmed losses. A request for an unavailable month should stay unavailable, rather than silently substitute another period.
> After deployment, endpoint discovery and a completed request establish connectivity. They do not, on their own, prove that a combined answer is reconciled. That requires comparison with the actual SQL results and retrieved policy passages.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 10-agent-hub — Agent Hub

Draft start 10:26 · target 69 seconds · 153 words · 5 seconds total silent proof hold within this chapter.

> In Agent Hub, we begin with a narrow portfolio question and then a queue question. The response should state its month and snapshot, show amounts in rupees, and retain the distinction between total gross activity and flagged gross.
> We then ask a policy question that tests the exact flag boundary and both alternatives in the priority rule. This gives the analyst an inspectable explanation of why an account enters the review queue.
> A combined investigation should bring the portfolio, selected account, bounded evidence, and retrieved policy into one brief. It must also state what remains unavailable and where human review is needed.
> Successful Agent Hub use has been reported for the prepared prompts. For this publication, we record the responses and reconcile them again. The available trace export contains only the root, so it does not prove every internal tool call. The proof shown to the viewer must match the evidence actually captured.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 11-streamlit — Streamlit copilot

Draft start 11:35 · target 101 seconds · 225 words · 7 seconds total silent proof hold within this chapter.

> The Streamlit application provides a focused analyst entry point to the published agent. Connection checks the agent card before chat is enabled. The recording keeps credentials and the private endpoint out of view.
> For the demonstration, we prepare prompts for portfolio context, the queue, policy, and the investigation brief. They are recording aids; the film should not imply that a prompt-picker control exists unless that control is visible in the current application.
> A follow-up such as “for that same account and month” should preserve the existing conversation context. The client sends the returned A two A context identifier with the next message, and the application keeps conversation history within its configured scope. Starting a new chat is a deliberate reset. This behavior does not claim permanent server-side memory.
> There is a publication acceptance gate here. In the historical test, the connection, SQL response, and follow-up transport succeeded, and context was preserved. However, the hybrid answer's transaction rows conflicted with the reference for the same account, month, and snapshot. That answer is not a validated investigation brief.
> Before showing a successful combined answer, we must reconcile a fresh hosted run against its tool results and policy passages. If it does not reconcile, we show the limitation clearly and stop the success narrative at the validated SQL and connectivity steps. The analyst's trust depends on this check.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## 12-close — The decision remains evidence-led

Draft start 13:16 · target 43 seconds · 92 words · 4 seconds total silent proof hold within this chapter.

> The demonstration brings an analyst from a portfolio question to a review priority, supporting records, and an applicable policy. The data foundation makes those facts available; the agent and application help organize them in the context of the analyst's question.
> The next step is a controlled proof of concept with the organization's own definitions, data permissions, reconciliation checks, and acceptance cases. Success means an investigation brief that a reviewer can verify. It does not mean that a fluent answer, a screening flag, or a completed request has already proved the business outcome.

Production cue: use the chapter card briefly, then the recorded proof. Keep the pointer still during the silent hold. Do not read loading spinners or imply that a shortened wait was real-time.

## Optional replacement after hosted hybrid acceptance passes

This is an alternative to the final two paragraphs of chapter 11, not additional narration. Use only after the acceptance record identifies the tested deployment, period, account, snapshot, exact SQL result files, retrieved policy passages, context continuity, and reviewer. Re-time the chapter after replacing it.

> In this recorded run, the combined answer has been checked against the portfolio and account tool results, the returned transaction groups, and the retrieved policy passages for the same reporting scope. The brief retains the exact amounts, sample limits, and policy conditions. The follow-up also preserves the account and month in this conversation.

> The analyst can now inspect the structured evidence and policy together before deciding what further review is needed. This is an evidence-backed draft for human review. No external action is executed.
