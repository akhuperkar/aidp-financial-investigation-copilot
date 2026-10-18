# Video production package

**Footage, voice, captions and final MP4 are pending.** This folder contains a complete recording and edit plan, not a rendered video. The primary narration is 1,845 spoken words. At 140–150 words per minute it takes about 12.3–13.2 minutes to read; 69 seconds of planned proof holds give a **provisional 13:59 cut** at the 145-word target. Actual voice and footage determine the final duration.

| File | Purpose |
|---|---|
| [recording-guide.md](recording-guide.md) | Ordered capture actions, environment preparation, draft prompts, input naming, evidence checks, acceptance pause, captions and export |
| [narration.md](narration.md) | Full business-first female-English narration, timing notes and gated replacement after hosted hybrid acceptance |
| [storyboard.csv](storyboard.csv) | Thirteen chapters, exact proof/action, target duration, hold time, source reference and safe caption position |
| [youtube-metadata.md](youtube-metadata.md) | Draft title alternatives, description, tags, thumbnail text, caption language and provisional chapter plan |
| [youtube-metadata.json](youtube-metadata.json) | The same metadata in a structured format; final URL/ID placeholders remain pending |
| [input-manifest.example.json](input-manifest.example.json) | Honest missing-input manifest; unknown source paths remain `null` |
| [cards/](cards/) | Editable 1920×1080 cover/context/close and ten chapter dividers, plus a 1280×720 thumbnail SVG |
| [assemble.py](assemble.py) | Optional local FFmpeg helper for genuine, reviewed chapter cuts; strict preflight, no placeholder output |
| [caption-calibration.md](caption-calibration.md) | Measured ASS coordinate fix and the current local libass rendering dependency |
| [final/README.md](final/README.md) | Required final master path and remote LFS delivery check |

The narrative follows the analyst's decision: a review queue, the supporting account evidence, and the applicable policy. It distinguishes the verified Gold/Oracle Analytics publication from the dedicated agent snapshot. The separate ML training example does not score the agent queue or establish production fraud performance. Flags and P1 priority remain screening measures. No external actions or implemented approval workflow are demonstrated.

The historical Streamlit hybrid request completed and preserved context but **failed evidence reconciliation**. A successful combined-answer segment requires a fresh hosted acceptance record. The default narration and metadata keep that limitation visible; there is a gated alternative if a current run passes. See the [recording gate](recording-guide.md#hybrid-acceptance-pause) and the integrated [hosted acceptance procedure](../docs/hosted-acceptance.md) when supplied.

Record in chapter order, retain original footage privately under ignored `source/`, and fill a copy of the manifest only with real inputs. Integration supplies the diagrams/screenshots. The provided Oracle wordmark is present at `../media/brand/oracle-wordmark.png`; the SVGs reference that local artwork and contain no remote assets or invented UI. No TTS, MP4, YouTube upload or Medium publication has been produced here.

The final reviewed master must be `video/final/aidp-financial-investigation-copilot.mp4` in both the local public repository and the remote Git LFS store. A Git pointer alone is not the media delivery. Source footage stays out of the public repository. Use the final cut to replace every provisional chapter marker; then resolve or remove all pending URL lines before publishing the metadata.

Pending article: `{{MEDIUM_ARTICLE_URL}}`. Pending final video: `{{YOUTUBE_DEMO_URL}}` / `{{YOUTUBE_VIDEO_ID}}`.
