# Financial Investigation Copilot — final-cut narration

Approved voice: Kokoro af_heart, speed 0.86. Continuous takes per chapter; no voice acceleration.

## 00 · From signal to investigation

A flagged transaction is the start of an investigation. Which account needs attention, what happened, and which policy applies? At Meridian Demo Bank, we'll use Oracle AI Data Platform to connect transaction data, policy documents and specialist agents. Then we'll bring the investigation copilot to users in Agent Hub and Streamlit.

## 01 · Build the data foundation

Before an agent can answer those questions, it needs a useful data foundation. In Workbench, the Spark notebook organizes transactions into Bronze, Silver and Gold. Bronze keeps the incoming records. Silver validates them and adds time features. Gold prepares account-month analytics and transaction-level features.

A separate random forest exercise shows how those features can support model training and evaluation. The investigation queue in this demo uses screening rules.

We publish the Gold tables into Autonomous AI Lakehouse for executive analytics. Catalog, schema and table definitions remain configurable. The agent's SQL tools query prepared Spark serving tables derived from Gold.

## 02 · See the portfolio picture

The dashboards give us the portfolio picture before we open an individual account. The notebook and Oracle Analytics show activity, screening flags, exposure and concentration.

The investigation queue turns a broad portfolio signal into a short list for analyst review. Trends and exposure breakdowns add context: is the activity concentrated in particular accounts, transaction types or locations?

That is the handoff to the copilot. Take a focused question beyond the chart, and retrieve the records and policy behind it.

## 03 · Coordinate specialist agents

In Agent Builder, the flow starts with a message, a guardrails node and the investigation supervisor. The supervisor interprets the request and coordinates four specialists.

The portfolio SQL agent retrieves reporting context, monthly totals, trends and exposure mix. The investigation SQL agent retrieves ranked accounts, an account snapshot and transaction evidence. Seven predefined SQL tools keep aggregation and ranking in the data layer.

We can inspect a tool's query, input parameters and test result. This makes the connection between a business question and its data explicit.

The policy agent searches a curated knowledge base. Its RAG tool retrieves relevant passages and source references, adding business context alongside the structured evidence.

The brief agent uses a Prompt tool to organize the supplied facts and passages into an analyst draft. It is configured to preserve scope, show tables and identify missing information.

The value comes from coordination. Each specialist has a clear role, and the supervisor brings the required contributions back to the user's question.

## 04 · Work through an investigation

Let's start in the playground with a portfolio question. The response returns the reporting month, transaction activity and flagged exposure in a table. The source and reporting scope stay with the answer.

Next, we ask for the complete priority-one policy. The policy agent retrieves the threshold conditions and cites the document. Those conditions explain how an account enters the review queue.

Now we investigate the account with the highest flagged exposure. The draft separates account totals from supporting transactions, with amounts, dates, transaction types and screening scores. It also presents the relevant policy and proposed analyst review steps.

This gives the investigator a starting point for review, while the underlying records remain essential. A fluent draft still needs checking against its sources.

Testing matters at each layer: the SQL tool result, the retrieved policy passage, and the combined response. Focused follow-ups help us inspect the evidence and check what the agent can actually support before making it available to users.

## 05 · Deploy, describe and discover

After testing, the workflow is deployed on AI compute. The Agent Card describes what the copilot can do, with a version, a clear description and example questions.

Here, four skills cover portfolio analytics, account triage and transaction evidence, policy retrieval, and investigation briefing. Those skill descriptions help people understand when to use the agent.

Registering the deployed agent in AI Registry makes those capabilities discoverable, subject to its access permissions. The deployment provides an endpoint for applications to call. The card and registry connect that running workflow with the users and applications that need it.

## 06 · Ask questions in Agent Hub

In Agent Hub, users can find the copilot and ask a question without opening the builder. Here, a focused follow-up asks for the current transaction evidence behind an account's screening totals.

The response shows the supporting rows and policy context. This is where the analyst can inspect dates, amounts and scores, rather than relying on a summary alone. The output remains a draft for human review.

## 07 · Bring the copilot into Streamlit

The same deployed workflow can also sit behind a local Streamlit application. The application connects to the agent endpoint and presents a focused copilot interface.

Here, we review portfolio activity, then ask which accounts have the highest flagged exposure. The answer comes back as a readable table, with source and scope information.

The investigation capability stays with the deployed agent. The application controls how people interact with it. This brings connected data and policy context into an interface an analyst can use, while leaving the decision about further investigation with the analyst.

## 08 · Follow the evidence

We've connected a prepared data foundation, executive analytics and specialist agents into one investigation experience. The aim is to reduce the effort of searching for records, finding the right policy and assembling a review draft.

The notebooks, agent setup and application code are in the project repository. Start with a signal. Follow the evidence. Keep the analyst in control.
