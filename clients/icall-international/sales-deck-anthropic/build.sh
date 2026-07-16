#!/usr/bin/env bash
# Render index.html → slides_png/*.png → iCall_Anthropic_Annotation_Pitch.pptx
set -euo pipefail
cd "$(dirname "$0")"
/usr/bin/python3 render_slides.py
/usr/bin/python3 build_pptx.py
echo "→ iCall_Anthropic_Deployment_Partner_Pitch.pptx"
