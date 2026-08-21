#!/usr/bin/env bash
# Print the deck to a 1280x720 PDF via headless Chrome, then split
# each page into a slide PNG. Mirrors the workflow used for the SGP deck.
set -euo pipefail
cd "$(dirname "$0")"

CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
OUT="slides_png"
mkdir -p "$OUT"
rm -f "$OUT"/slide-*.png

TMPDIR="$(mktemp -d)"
PDF="$TMPDIR/deck.pdf"

"$CHROME" --headless --disable-gpu --no-pdf-header-footer \
  --print-to-pdf-no-header \
  --print-to-pdf="$PDF" \
  "file://$PWD/index.html" >/dev/null 2>&1

# 1280x720 @ 144dpi ≈ 1280*2 x 720*2 = 2560x1440 for retina crispness.
pdftoppm -png -r 144 "$PDF" "$OUT/slide"
# pdftoppm produces slide-1.png, slide-2.png ... rename to slide-01.png etc.
for f in "$OUT"/slide-*.png; do
  base="$(basename "$f")"
  num="${base#slide-}"; num="${num%.png}"
  new="$(printf 'slide-%02d.png' "$((10#$num))")"
  if [ "$base" != "$new" ]; then
    mv "$f" "$OUT/$new"
  fi
done

ls "$OUT"
