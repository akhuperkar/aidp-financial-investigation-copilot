# Caption coordinate calibration

Date: 18 October 2026. Private fixture: a two-line, one-second SRT with neutral calibration text. No source UI, demonstration footage, voice, final MP4 or published media was generated.

The installed FFmpeg 8.0.1 converted that SRT to an ASS script with `PlayResX: 384` and `PlayResY: 288`. At a 1080-pixel output height, a nominal 34-unit font in that script would be subject to a 1080/288 coordinate scale; it should not be treated as a 34-pixel font.

`assemble.py` now converts an SRT copy to a temporary ASS file and explicitly sets:

```text
PlayResX: 1920
PlayResY: 1080
WrapStyle: 2
```

The fixture verified all three header values and preservation of its explicit two-line break. The rendering style retains nominal `Fontsize=34`, bottom-center alignment, a 38-pixel bottom margin, 10-pixel box padding/outline, and a half-transparent black box (`&H80000000`). Actual application imagery remains above the reserved 160-pixel lower band. The original corrected SRT is still the delivered sidecar. The acceptance and source-review gates were not relaxed.

Pixel calibration remains pending: the actual 1920×1080 single-frame render attempt returned exit 8, `No such filter: 'subtitles'`. The installed FFmpeg and the checked versioned builds do not expose the libass subtitle renderer. No calibration PNG was created, so no measured glyph height or box bounds are claimed. Preflight now detects this missing capability before encoding.

Before rendering footage, select an FFmpeg build that lists the `subtitles` filter, rerun the two-line calibration on a neutral frame, and inspect that all caption pixels stay in the lower band (`y >= 920`). A nominal font size specifies the ASS coordinate size; individual glyph ink bounds depend on the selected font. Watch the complete final cut to confirm no controls or evidence are covered. The helper installs no dependencies.

The private test files were kept outside the repository at `/private/tmp/aidp-caption-calibration/`: `calibration.srt`, `baseline.ass`, `captions.ass`, and `render-attempt.log`. They are test evidence, not video inputs or delivery media.
