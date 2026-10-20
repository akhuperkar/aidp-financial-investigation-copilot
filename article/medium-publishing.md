# Medium article and repository copy

**Last synchronized:** 20 October 2026. [Open the Medium story](https://medium.com/@abhijit.khuperkar/73440372750f); the author view currently labels it **Draft**. [The demo video is published on YouTube](https://www.youtube.com/watch?v=7Jhn-jmz2vg). This repository refresh does not publish or change the Medium story.

## Current story

- **Title:** Building a Multi-Agent Financial Investigation Copilot with Oracle AI Data Platform
- **Subtitle:** Connecting financial data, policy documents and specialist agents — from a visual workflow to Agent Hub and Streamlit.
- **Author:** Abhijit Khuperkar
- [Canonical Markdown](medium-article.md), [public-link copy](medium-ready.md), [HTML preview](preview.html)
- [Source register](../docs/research-sources.md) and [references](references.json)

The article centers on multi-agent orchestration: four executor roles, seven SQL tools, policy RAG, brief composition, testing, Agent Card skills, deployment, AI Registry, Agent Hub and Streamlit. A compact data-foundation section and executive-dashboard section supply context. The methodology is summarized in a short closing note.

## Figures and cover

Article figures are stored in [media/](media/). They include the medallion responsibilities, complete architecture, executive dashboard, executor roles, Agent Builder flow, RAG configuration, investigation conversation, Playground, Agent Card/Registry, and Agent Hub/Streamlit.

Use [cover-medium-safe-v2.png](../media/cover-medium-safe-v2.png) for Medium's cover. It moves the text farther from the left edge; a centered 320:215 crop was inspected against the supplied preview. The [original cover](../media/cover.png) is preserved. Check the actual Medium preview after replacing the cover, since placements can crop differently.

The older optional table exports in [assets/](assets/) remain reusable assets; the revised article uses the compact medallion image instead of the old numeric reference table. Their presence does not mean they must be inserted into this article.

## Regenerate exports

From the repository root:

```bash
python3 article/build_medium_exports.py
# Optional HTML regeneration requires Pandoc:
pandoc article/medium-article.md --standalone --css preview.css --metadata 'pagetitle=Financial Investigation Copilot' --output article/preview.html
```

The Python script uses only the standard library and creates the absolute-link Markdown. It can also render the two legacy table SVGs when that table-based article format is supplied. The HTML preview uses relative assets and is a local review aid.

## Editorial boundaries

The story describes a workflow for analyst review. It does not claim confirmed fraud, measured losses or savings, calibrated probabilities, production model effectiveness, case creation or account restrictions. Keep the actual Spark-agent and AILH/OAC serving paths distinct. The separate random forest exercise does not supply the agent queue.

A fluent answer or successful endpoint request is not a new hosted acceptance result. The [hosted ledger](../docs/hosted-acceptance.md) and [methodology](../docs/metrics-and-methodology.md) retain the detailed implementation boundaries.
