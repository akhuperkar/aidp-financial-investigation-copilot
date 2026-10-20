# Financial Investigation Copilot demo video

[Watch on YouTube](https://www.youtube.com/watch?v=7Jhn-jmz2vg) · [Companion Medium article (draft)](https://medium.com/@abhijit.khuperkar/73440372750f)

The author published the approved **motion version 2** on 20 October 2026. It follows the same storyboard, neural female narration and caption timing as the first cut, with advancing screen recordings for application navigation, configuration scrolling, questions and responses.

**7:10.5 · 1920 × 1080 · 30 fps · H.264/AAC**

| Artifact | Purpose |
|---|---|
| [Captioned master](final/aidp-financial-investigation-copilot.mp4) | The published motion edit with visible captions |
| [Clean master](final/aidp-financial-investigation-copilot-clean.mp4) | Same video and narration, without visible captions |
| [English subtitles](final/aidp-financial-investigation-copilot.en.srt) | SRT for the clean master |
| [Chapter timestamps](final/chapters.txt) | Nine final chapter markers |
| [Final narration](final/narration.md) | Exact spoken script |
| [Voice profile](voice-profile.json) | Approved neural female voice and caption styling |
| [YouTube metadata](final/youtube-metadata.md) | Title, description, tags and current links |
| [Quality checks](final/quality-check.json) | Full decode, media hashes, unchanged audio/captions and footage policy |
| [Thumbnail](final/youtube-thumbnail.jpg) | 1280 × 720 YouTube artwork |

## Story sequence

1. From signal to investigation
2. Build the data foundation: medallion, separate ML exercise and AILH publication
3. See the portfolio picture in notebook and Oracle Analytics
4. Coordinate specialist agents and tools
5. Work through an investigation
6. Deploy, describe and discover: Agent Card and AI Registry
7. Ask questions in Agent Hub
8. Bring the copilot into Streamlit
9. Follow the evidence

The platform chapters contain 61 real recording segments, with no artificial still-frame holds or platform screenshot loops. The cover, architecture overview, chapter dividers and closing remain designed graphics. Waiting and setup are trimmed; selected browsing is accelerated while narration stays at the approved pace. The edit is not an execution-time benchmark.

## Download

```bash
git clone https://github.com/akhuperkar/aidp-financial-investigation-copilot.git
cd aidp-financial-investigation-copilot
```

The finished MP4s are stored directly in Git because the account's LFS budget was exhausted at publication. They are about 54.3 MiB and 49.7 MiB, each below [GitHub's regular Git file limit](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github). A normal clone includes the videos; expect roughly 104 MiB of additional media. Raw recordings and local render caches are excluded. Future larger distributions can use release assets or a funded LFS allowance.

The earlier [recording guide](recording-guide.md), [original storyboard](storyboard.csv), [input manifest template](input-manifest.example.json), [caption calibration notes](caption-calibration.md) and [editable cards](cards/) remain production references. Use the final script and final chapter timestamps for the published cut rather than their provisional timings.

Screening measures support analyst review. No external operational action or independently validated fraud-detection performance is demonstrated. Detailed boundaries remain in the [methodology](../docs/metrics-and-methodology.md) and [hosted acceptance record](../docs/hosted-acceptance.md).
