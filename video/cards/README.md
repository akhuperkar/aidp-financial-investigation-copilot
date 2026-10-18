# Editable cards

The 13 numbered SVGs are editable text artwork at 1920×1080. They contain no invented product UI. `thumbnail.svg` is 1280×720. The ten platform chapter dividers run from `02-bronze.svg` through `11-streamlit.svg`; cover, context, and close are additional cards.

Palette: warm paper `#F5F1E9`, charcoal `#312D2A`, muted text `#625C55`, Oracle red accent `#C74634`; Bronze `#8C6743`, Silver `#747C83`, Gold `#A1812B`. Typography uses local Arial/Helvetica fallbacks. These are Redwood-aligned production assets, not an assertion of an official Oracle template.

Each card references the supplied raster wordmark at `../../media/brand/oracle-wordmark.png`. Resolve that local asset before export; do not fetch or reconstruct a logo. If an editor does not resolve relative SVG image references, embed that supplied PNG during import. The source SVG remains editable and keeps the real supplied artwork. No remote resources or scripts are used.

Use a 1.5–2.5 second chapter card inside each chapter's target duration, with a 0.2–0.35 second dissolve into actual footage. Keep text visible through the transition. Cover may hold for 6–10 seconds. Do not extend footage by looping still cards to reach a target runtime.
