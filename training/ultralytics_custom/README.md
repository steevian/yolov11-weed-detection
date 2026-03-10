# ultralytics_custom

This directory is reserved for a local editable copy of Ultralytics for phase3/phase4 model customization.

Why this exists:
- Keep training framework modifications isolated from Flask inference environment.
- Avoid changing site-packages directly.

Recommended next step:
1. Copy your local `ultralytics` package source into this directory.
2. Apply MobileNetV3 and ECA module registration changes here.
3. Use `PYTHONPATH` or editable install to point phase3/phase4 scripts to this copy.
