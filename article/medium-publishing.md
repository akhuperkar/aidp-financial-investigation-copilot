# Medium publishing handoff

**Status:** draft prepared for review; no Medium or YouTube publication is claimed.

**Word count:** 1,621 words, excluding image alt text and link URLs.

## Copy

- **Title:** Why a Financial Investigation Copilot Starts with the Data Foundation
- **Subtitle:** An evidence-led analyst workflow with Oracle AI Data Platform, Autonomous AI Lakehouse and Oracle Analytics Cloud
- **Author:** Abhijit Khuperkar
- **Draft date:** 18 October 2026
- **Suggested tags:** AI; Data Engineering; Oracle Cloud; Financial Services; Generative AI
- **Article:** [medium-article.md](medium-article.md)
- **Local preview:** [preview.html](preview.html)
- **Source register:** [research-sources.md](../docs/research-sources.md)
- **Structured references:** [references.json](references.json)

**Suggested preview description:** A practical financial investigation workflow showing how Spark medallion data, Oracle Analytics Cloud, bounded SQL tools and policy retrieval support an evidence-led analyst brief.

## Images, order and alt text

The article uses four figures. Preserve the dataset note before the first numeric table. Captions explain each visual's purpose; alt text describes its content. Upload the supplied crisp PNG exports to Medium; the editable SVG originals remain in the repository. Check label readability in the publication preview.

| Figure | Repository asset | Alt text |
|---|---|---|
| 1 | [executive-snapshot.png](../media/screenshots/executive-snapshot.png) | Meridian Demo Bank executive snapshot for December 2024, showing portfolio activity and rule-based review measures. |
| 2 | [architecture.png](../media/diagrams/architecture.png) | Architecture showing Spark Bronze, Silver and Gold processing, Gold publication to Autonomous AI Lakehouse and OAC, a separate Spark snapshot path for SQL tools, and policy retrieval for the agent. |
| 3 | [investigation-queue.png](../media/screenshots/investigation-queue.png) | December investigation queue with accounts ordered by flagged gross activity and separate rule-based priority labels. |
| 4 | [agent-flow.png](../media/diagrams/agent-flow.png) | Agent flow separating portfolio SQL, investigation SQL, policy retrieval and brief composition, with source context and human review. |

**Suggested cover:** architecture diagram, with the title kept as publication text rather than baked into the diagram. Review the final crop before saving.

## Placeholder and publication checks

- [ ] Review the article, final screenshots and diagram labels together. Check that OAC's December figures match the reference table.
- [ ] Verify that screenshots contain no endpoints, credentials, session identifiers, personal browser details or unrelated content.
- [ ] Confirm the public companion repository is reachable; replace the article's relative `../README.md` link with its verified public URL.
- [ ] Record and review the walkthrough. Replace `{{YOUTUBE_DEMO_URL}}` with the actual public or unlisted video URL only after it exists and plays correctly. If publication proceeds without a video, remove the pending-video sentence explicitly; do not substitute an invented URL.
- [ ] Run the [hosted acceptance checks](../docs/hosted-acceptance.md) before representing a new hybrid answer as reconciled. If acceptance is still pending, retain the article's current evidence wording.
- [ ] Transfer headings, both tables, four images, captions and source links into Medium. Check column alignment and threshold symbols after paste.
- [ ] Verify the Gartner and McKinsey links remain attached to the correct dated survey populations. Keep the methodology intact.
- [ ] Check mobile and desktop previews, including diagram text, account IDs and INR amounts.
- [ ] Review title, subtitle, author, tags and cover crop in the final publication preview.
- [ ] Publish only when authorized. Record the resulting actual Medium URL in the repository publication record after it exists.

## Editorial guardrails

The story demonstrates an investigation workflow and an enterprise data foundation. It does not claim validated production fraud detection, predicted losses, measured savings, automated account action or an implemented approval gate. Preserve the separate OAC and deployed-agent snapshot paths. Present the random forest as a separate notebook exercise; it does not score the agent's queue.

Do not add the unverified 83% statistic or reinterpret 88% AI adoption as workflow disconnection. The article deliberately uses only the independently verified Gartner and McKinsey findings recorded in the source register.
