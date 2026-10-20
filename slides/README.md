# Presentation

- `aidp-financial-investigation-copilot.pptx`: 10-slide editable Redwood presentation.
- `index.html`: offline interactive slide cards; open directly in a browser. Use **Present**, arrows, **N** for notes, or **Print / PDF**.
- `deck-content.json`: slide copy, citations and speaker notes.
- `build_html.py`: regenerate the HTML with Python's standard library.
- `previews/`: rendered PNGs used for visual review.

The PPTX uses the FY26 Oracle blank-template pipeline, with editable architecture and agent diagrams added as native shapes and connectors. The OAC screenshot remains an embedded image of the verified reference. Research citations and implementation limits are in speaker notes. Template-internal classification labels were removed from this public derivative. The terminal Oracle closing slide is display-only.

To revise the HTML, edit `deck-content.json` and run `python slides/build_html.py` from the repository root. The PPTX remains editable in PowerPoint; the optional Redwood generator is a separate authoring tool, not required to use the notebooks or application.

## Companion publications

[Watch the published demo](https://www.youtube.com/watch?v=7Jhn-jmz2vg) · [Read the companion article (currently Draft)](https://medium.com/@abhijit.khuperkar/73440372750f). The technical slides retain their dated reference scope; current publication assets are in [video/](../video/README.md).
