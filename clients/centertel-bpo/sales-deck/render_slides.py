"""Render each .slide section of index.html → slides_png/slide-NN.png (1280x720 @ 2x)."""
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC_DIR = Path(__file__).resolve().parent
HTML    = SRC_DIR / 'index.html'
OUT_DIR = SRC_DIR / 'slides_png'
SLIDE_W, SLIDE_H, SCALE = 1280, 720, 2


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': SLIDE_W, 'height': SLIDE_H},
                                  device_scale_factor=SCALE)
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until='networkidle')
        page.evaluate('document.fonts.ready')

        slides = page.query_selector_all('.slide')
        print(f'Found {len(slides)} slides → {OUT_DIR}')
        for i, slide in enumerate(slides, start=1):
            out = OUT_DIR / f'slide-{i:02d}.png'
            slide.scroll_into_view_if_needed()
            slide.screenshot(path=str(out), omit_background=False)
            print(f'  {out.name}')
        browser.close()
    print(f'Done — {len(slides)} PNGs')


if __name__ == '__main__':
    main()
