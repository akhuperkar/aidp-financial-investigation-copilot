> Historical capture-planning reference. The published motion cut, final script and actual chapter timestamps are in [video/README.md](README.md) and [final/](final/). Provisional durations and pending-generation statements below describe the planning stage.

# Recording guide — financial investigation copilot

**Status: recordable production plan; source recordings are pending.** The base narration is 1,845 spoken words, with a provisional 13:59 edit at 145 words per minute and 69 seconds of proof holds. Record in the chapter sequence below. The ten platform chapters are Bronze, Silver, Gold, ML, AI Lakehouse, notebook plus Oracle Analytics, Agent Builder, testing/deployment, Agent Hub, and Streamlit.

## What the viewer should be able to decide

The story follows one business question: **which accounts should an analyst investigate first, what evidence supports that priority, and which policy applies?** The analyst is preparing a review, not certifying fraud or authorizing an external action.

| Outcome flow | Background work | Foreground evidence and decision | AI contribution | Application contribution | Memorable proof |
|---|---|---|---|---|---|
| Establish the review queue | Bronze/Silver/Gold transformations, metric definitions and verified analytical publication | Portfolio context and ranked queue; analyst selects an account to inspect | No AI claim is needed for deterministic calculations | Consistent reporting grain and visible source scope | Gross, net, flagged gross and count-based flag rate retain their definitions |
| Explain an account's priority | Dedicated agent snapshot plus predefined SQL tools; fictional policy corpus | Exact account totals, bounded transaction evidence and complete priority rule; analyst requests further evidence | Interpret a question, retrieve policy, organize a sourced explanation | Route the question to bounded tools and preserve month/account/snapshot | Same-named fields and the complete AND/OR rule agree with the source |
| Continue the investigation | Published endpoint, signed agent-card check and scoped conversation state | Follow-up referring to the same account and month; analyst reviews a draft | Summarize the requested evidence in context | Carry A2A context and show the response/history together | Context continuity and content reconciliation are checked separately |

Each flow starts with the operating problem and analyst context, explains why the decision matters, shows what preparation already happened, and ends with the review decision, work reduced, and proof. Do not turn the platform chapters into an unrelated feature tour. No time-saving percentage, realized saving, prevented loss, or business-impact number is established by this demo.

## Prepare the recording environment

1. Use a demonstration tenant and the existing data. Do not re-run generation, rebuild source tables, publish replacements, change clustering, or execute optional DDL during the recording. Capture existing verified results or read-only queries.
2. Close notifications, unrelated tabs, email/chat, password-manager popups, bookmarks and account menus. Use a clean browser profile if available. Hide the desktop and dock. Do not display wallets, OCI configuration, bearer tokens, private keys, passwords, signed request headers, real customer information or endpoint identifiers.
3. Preload the correct existing notebook, OAC view, flow, Hub and Streamlit application. Set browser zoom so table labels and the final two decimal places remain readable after the reserved caption band is added. Capture at 2560×1440 or higher if practical, otherwise clean 1920×1080; 16:9, 30 fps, constant frame rate, maximum quality. Turn off microphone capture for silent UI footage.
4. Record two seconds of stillness before and after each action. Hold stable proof screens for the storyboard's total proof-hold allowance. Move the pointer deliberately, then park it away from figures, citation text and controls. Scroll in short movements with reading pauses.
5. Record complete response waits in the source. The final cut may shorten waits with a visible dissolve and the small caption “Response wait shortened.” Never imply an edited wait is a measured response-time claim. Keep a private timestamp/acceptance log for the uncut request.
6. Record a backup take of each proof screen. Preserve uncut originals locally under `video/source/`. Root integration must keep that directory ignored; private acceptance exports also stay out of the public repository.

## Input naming and handoff

Use this naming pattern:

```text
video/source/2026-10-18/00-cover_take-01.mp4
video/source/2026-10-18/01-context_take-01.mp4
video/source/2026-10-18/02-bronze_take-01.mp4
...
video/source/2026-10-18/11-streamlit_take-01.mp4
video/source/2026-10-18/12-close_take-01.mp4
video/source/2026-10-18/voice-female-en_take-01.wav
video/source/2026-10-18/captions-en-reviewed.srt
video/source/2026-10-18/acceptance-private.json
```

The date is illustrative; use the actual recording date. Include chapter slug and take number; do not include a token, endpoint ID or customer name in a filename. Notes should identify actual source scope and redact private infrastructure identifiers before any public copy.

Copy `input-manifest.example.json` to `video/source/input-manifest.json`. All unknown paths start as `null`; fill only paths that exist. Paths are relative to `video/`, not to the manifest's folder. Each `clips[].source_path` identifies the retained raw recording; `clips[].path` identifies the reviewed chapter cut, including its card, genuine footage and intentional transitions. The assembly helper takes these reviewed cuts, not arbitrary raw recordings. `in_seconds`/`out_seconds` define the selected range in that reviewed cut. Record source takes and trims honestly.

Do not fill a missing chapter by looping a screenshot, duplicating footage, inventing a product UI, or adding an empty MP4. Cards can be rendered from the supplied editable SVG artwork as brief design elements; they do not replace the missing UI recording.

## Chapter capture sequence

The exact action/proof/hold targets live in `storyboard.csv`. The following operator notes identify the relevant source sections. Public repository paths are relative to this folder; source-workspace references are explicitly labelled.

| Chapter | Record | Hold and inspection point |
|---|---|---|
| 00 Cover | `cards/00-cover.svg`, then a dissolve to the context diagram | Keep the question readable; the cover chapter includes its spoken question, so do not assume the whole chapter is a silent title card |
| 01 Context | `../media/diagrams/architecture.svg` and `medallion.svg`, once supplied by integration | Make the AILH-to-OAC path and dedicated agent snapshot distinguishable; show “Demonstration dataset; amounts shown in USD” near the first numbers |
| 02 Bronze | Existing medallion notebook, “Bronze Layer: Raw Data Ingestion,” schema/table and bounded sample | Show exact account ID, signed amount and source timestamp. Do not execute data generation |
| 03 Silver | “Silver Layer: Data Cleaning and Validation,” transformation logic and sample | Preserve the source meaning while showing validation/enrichment; do not equate schema cleanliness with completeness of business context |
| 04 Gold | “Gold Layer: Analytics and ML-Ready Data,” the two table definitions and verified reference | Distinguish transaction grain from account-month grain; label the date/version beside historical counts |
| 05 ML | “Gold Layer: ML Model Training and Evaluation,” label derivation, features, split, fit and evaluation code | Show `is_fraud = risk_score > 60` and that `risk_score` is not an input feature. Show random-score generation before any evaluation metric |
| 06 AILH | Existing AILH notebook appendix, mapping/configuration, pinned versions and initial publication readback/checks | Show both tables and full-row comparison. Do not present a dry run as a write test or a failed refresh as successful |
| 07 Notebook + OAC | Executive analytics notebook, then existing OAC workbook: executive snapshot → activity/risk trends → investigation queue → monthly changes → risk exposure | Keep December 2024 filter and source label visible. Capture account `ACC00004535` and flagged gross `USD 28,008.03` in the verified reference |
| 08 Agent Builder | Existing `FS_INVESTIGATION_SUPERVISOR` flow and its SQL/RAG/brief paths; one tool's parameters and fictional corpus | Use current tenant UI labels. The diagram is reference artwork; do not imply it is a live trace |
| 09 Testing/deployment | Narrow response checks and existing deployed state, with endpoints masked | Show requested scope, expected boundary and actual outcome together. Status/URL proves neither inner execution nor answer correctness |
| 10 Hub | Portfolio → queue → narrow policy prompt; full brief only after reconciliation | Keep sources and period/snapshot readable; retain exported actual outputs privately |
| 11 Streamlit | Connect off-camera → narrow portfolio answer → scoped follow-up → either accepted hybrid or explicit limitation branch | Show context continuity without exposing full private IDs. Apply the gate below; do not replay the historical failed hybrid as a validated result |
| 12 Close | `cards/12-close.svg`; repository/article labels only after they exist | End on the controlled POC and reviewer-verifiable result; keep human review/no external action clear |

Notebook names expected in the public repository:

- `../notebooks/financial_services_medallion_architecture_demo_ailh.ipynb` — medallion, ML and AILH appendix. Original saved outputs can be historical.
- `../notebooks/financial_services_executive_analytics_dashboards_aidp.ipynb` — executive calculations and reconciliation.
- `../notebooks/financial_services_multi_agent_demo_setup_aidp.ipynb` — dedicated semantic snapshot and SQL-tool setup.

If integration places a file elsewhere, update the link rather than inventing an asset. Chapter illustrations and screenshots are pending integration; the supplied wordmark is present. A source filename is a recording reference, not proof that the screenshot already exists.

### Numeric evidence for the OAC chapter

The verified 17 October 2026 Gold reference uses source Delta version 4, January–December 2024: 149,658 transaction rows; 52,735 account-month analytics rows; 5,000 accounts. December: 12,699 transactions; 4,436 active accounts; gross USD 31,642,312.97; net USD 20,071,594.45; 4,934 rule flags; flag rate 38.853453027797464%; flagged gross USD 12,547,752.55; 528 P1 accounts. Top queue account: `ACC00004535`, flagged gross USD 28,008.03. Values may be rounded for speech, but show exact values in evidence.

These are the Gold/OAC reference values, not expected answers for an older agent snapshot. If recording a refreshed source, update the source record, script, captions and metadata consistently. Do not silently force a current screen to match a historical reference. Do not combine the older agent's 12,566-transaction December snapshot with these OAC figures.

## Prepared prompts — recording aids, not invented controls

Use a text file beside the recorder or paste into the existing chat input. These are drafts derived from the source-workspace `live_review/sample_prompts.txt`; confirm that the current deployment accepts the wording. They do not authorize changing prompts, deployment, tools or data. If the current app has no suggested-prompt picker, do not add one to the film.

1. **Portfolio:** “For the latest observed month, show portfolio transaction count, active accounts, gross activity, flagged gross and flag rate in a USD Markdown table. Include the period and source snapshot.”
2. **Queue:** “Rank the top five accounts by flagged gross exposure for the latest observed month. Show account, demo priority, transaction count, rule flags, flagged gross USD and flag rate in a Markdown table.”
3. **Policy boundary:** “Retrieve FS-POL-001 sections 1 and 2. Is score 60 flagged? State every condition that makes an account-month P1, preserving AND/OR logic and all amount and score thresholds. Cite the retrieved document/version/section.”
4. **Combined brief:** “For the latest observed month, investigate the highest-exposure flagged account. Combine the exact portfolio and account SQL totals, five transaction-evidence patterns, and the applicable retrieved triage policy. Return a USD Markdown analyst brief with separate portfolio/account tables, policy citations, evidence gaps and human-review steps.”
5. **Same conversation:** “For that same account and month, show five transaction-evidence patterns in a Markdown table. State duplicate multiplicity and whether the returned list is complete; use the account snapshot for total exposure.”
6. **Unavailable facts:** “Show confirmed fraud loss, fraud probability and the cash balance of the top account. Distinguish any available risk-screening measures from unavailable facts.”
7. **Unavailable period:** “Prepare the account-risk report for June 2026. Do not substitute another reporting period if June 2026 is unavailable.”

For a decisive proof sequence, resolve latest once, record the returned month/snapshot, and use that explicit scope in subsequent requests. Keep the same conversation for prompt 5. A separate new chat should reset the context; do not assert cross-session persistence from a single in-session follow-up.

## Hybrid acceptance pause

**Pause the combined-answer success recording if its content has not reconciled.** The historical record reports successful transport/context continuity but `content_validation.status = not_passed`: transaction rows conflict with the Agent Hub reference for the same account, period and snapshot. The root cause is unverified. A completed task is insufficient to reverse that finding.

Before using the optional success narration, retain a fresh acceptance record that includes:

- UTC run time, private deployment reference, client/Hub used, conversation/context continuity and actual task outcome.
- Returned period, exact account ID, snapshot ID and rule version. The queue and account snapshot must agree on `flagged_gross_usd`; total gross must not be substituted.
- Exact portfolio/account SQL result files, actual transaction-evidence groups, signed amounts, timestamps, scores, labels and duplicate multiplicities. Distinguish returned groups, total groups and cap; do not sum a bounded sample as complete exposure.
- Actual retrieved FS-POL-001 version/section passages. Score 60 is not flagged. P1 means flagged gross ≥ USD 10,000 **OR** at least one transaction with score ≥85 **AND** absolute amount ≥ USD 5,000. Verify the retrieved source itself; a generated summary is insufficient.
- Missing-data and unavailable-period behavior; no invented balance, KYC, counterparty, calibrated fraud probability, confirmed loss, filing or approval.
- A reviewer and explicit outcome for content reconciliation, kept separate from transport success. The public recording should show the accepted proof or the limitation.

Use `../docs/hosted-acceptance.md` for the integrated acceptance procedure when supplied. No fresh live retest was performed while creating this package.

If the gate fails or remains pending, retain chapter 11's default narration and the description's acceptance note. A limitation-led cut can show validated connectivity/SQL/context behavior and state the unresolved content gap. Do not use “validated end-to-end investigation” in its title, thumbnail, voiceover or post.

## Voice and caption production

Record or generate the final voice only after the chapter script is reviewed and the acceptance branch is selected. Use a clear adult female English voice, moderate 140–150 words per minute, with a target of 145. Keep pronunciation consistent and allow pauses for tables and policy logic. Do not imitate a real person's voice. No TTS was generated for this package.

Prefer 48 kHz, 24-bit WAV for the voice master. Edit breaths and clipping gently; retain natural cadence. No music is required. If music is later requested, use a licensed track at a level that leaves speech unambiguous and retain its attribution/license. Do not add a remote asset or telemetry dependency.

Create an English UTF-8 SRT from the final voice, then correct it manually against the final edit. Preserve account leading zeros, $/USD, dates, two-decimal amounts, “strictly greater than,” and the P1 AND/OR logic. Do not place raw tokens or private identifiers into captions.

For a 1920×1080 final, reserve a lower band of at least 140 pixels before adding captions. Keep actual application imagery above it rather than placing text over the last row, chat input or notebook controls. Target a 32–36 pixel visible caption font, at most two lines, approximately 42–55 characters per line, white text on a translucent charcoal box. Use a sans-serif font, a stable lower-center position, and readable in/out timing; keep box width inside 90% of the frame. The assembly helper uses a 160-pixel band and a nominal 34-pixel ASS font. It converts a temporary copy of the SRT to ASS, sets `PlayResX=1920`, `PlayResY=1080` and `WrapStyle=2`, and retains the original SRT for delivery. This avoids scaling a 34-unit caption from FFmpeg's smaller default script resolution. Inspect the actual rendered font and two-line cues for overflow. Adapt the design after seeing footage if any meaningful control is covered.

Keep the dataset/USD note visible in context and methodology, and screening-versus-confirmed-fraud language near conclusions. Captions must faithfully represent the spoken voice; do not insert a caveat solely as tiny text while the voice makes an unsupported claim.

## Edit and export

Build chapter cuts from genuine source footage and the editable cards, using short dissolves between chapters. Fit the voice to real action, not arbitrary loops. A target duration is planning guidance; a readable proof screen takes precedence over an exact draft time.

`assemble.py` is an optional offline helper for already reviewed chapter cuts. It fails before rendering if footage, voice, corrected SRT, acceptance evidence, or review fields are missing. It normalizes the clips, reserves the caption band, concatenates their actual selected ranges and muxes the full voice. It does not manufacture cards, generate speech, fix evidence, publish, or certify correctness. Its strict assembly check relies on the producer's recorded review; still watch the complete output.

```text
python3 video/assemble.py --manifest video/source/input-manifest.json --check
python3 video/assemble.py --manifest video/source/input-manifest.json --render
```

Run these from the public repository root. FFmpeg and ffprobe must already be installed, and FFmpeg must expose the libass `subtitles` filter; the helper installs nothing. The current local FFmpeg build lacks that filter, so preflight blocks rendering until a suitable existing build is selected. See `caption-calibration.md` for the measured script-resolution test and the pixel-render limit. The example manifest deliberately fails because every missing media path is `null`.

Deliver H.264 high-quality MP4, 1920×1080, 30 fps, yuv420p, AAC 48 kHz, `faststart`; keep a separate lossless voice master and corrected SRT. The helper uses CRF 16, `slow`, AAC 256 kbit/s. A separate later 4K export is optional only if source resolution supports it. Verify no blurred digits, clipped audio, wrong aspect ratio, caption/control overlap, or unlabelled wait cuts. Watch the entire encoded MP4 with sound.

Final master: `video/final/aidp-financial-investigation-copilot.mp4`. Final English sidecar: `video/final/aidp-financial-investigation-copilot.en.srt`. Measure chapter starts from that file, then update both YouTube metadata files. The final MP4 must exist in the local public repository and its media object must be retrievable from remote Git LFS before delivery is described as complete. Root integration owns Git/LFS, uploads, publication, and final URL updates.
