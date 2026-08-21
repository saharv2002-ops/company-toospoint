#!/usr/bin/env bash
# Render index.html → slides_png/*.png → CenterTel_BPO_Sales_Deck.pptx
set -euo pipefail
cd "$(dirname "$0")"
/usr/bin/python3 render_slides.py
/usr/bin/python3 build_pptx.py
/usr/bin/python3 build_pdf.py
echo "→ CenterTel_BPO_Sales_Deck.pptx"
echo "→ CenterTel_BPO_Sales_Deck.pdf"
