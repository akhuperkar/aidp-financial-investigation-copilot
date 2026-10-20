# Published motion master

[Watch on YouTube](https://www.youtube.com/watch?v=7Jhn-jmz2vg) · [Companion Medium article (draft)](https://medium.com/@abhijit.khuperkar/73440372750f)

The approved **motion version 2** is stored under stable final filenames:

- [aidp-financial-investigation-copilot.mp4](aidp-financial-investigation-copilot.mp4) — captioned master
- [aidp-financial-investigation-copilot-clean.mp4](aidp-financial-investigation-copilot-clean.mp4) — same edit without visible captions
- [aidp-financial-investigation-copilot.en.srt](aidp-financial-investigation-copilot.en.srt) — English subtitles
- [chapters.txt](chapters.txt), [narration.md](narration.md), [youtube-metadata.md](youtube-metadata.md)
- [quality-check.json](quality-check.json) — encoded-file hashes and verification

**7:10.5 · 1920 × 1080 · 30 fps.** Both MP4s passed full decoding without errors. Their narration AAC packets and subtitle bytes match the approved first cut. The application chapters use advancing recordings; brief design cards are retained. Original recordings and the earlier review edit remain outside this public repository.

The two MP4s are stored directly in Git and are included in a normal clone. The account's LFS budget was exhausted, so this release avoids LFS dependency for the completed videos. Their SHA-256 hashes are recorded in the quality report and package manifest. Publication links and state are in [data/publication.json](../../data/publication.json).
