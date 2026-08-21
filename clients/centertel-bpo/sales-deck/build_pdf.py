"""Export the sales deck to a single 16:9 PDF, one slide per page.

PDF is the most portable format for macOS (Preview, Keynote) and iOS
(Files, Mail, Safari) — no PowerPoint required.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright

SRC_DIR = Path(__file__).resolve().parent
HTML    = SRC_DIR / 'index.html'
OUT     = SRC_DIR / 'CenterTel_BPO_Sales_Deck.pdf'

# 16:9 at 1280x720 CSS px → 13.333in x 7.5in
PAGE_W_IN, PAGE_H_IN = 13.333, 7.5


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        ctx = browser.new_context(viewport={'width': 1280, 'height': 720},
                                  device_scale_factor=2)
        page = ctx.new_page()
        page.goto(HTML.as_uri(), wait_until='networkidle')
        page.evaluate('document.fonts.ready')

        # Force each .slide onto its own PDF page and strip the deck padding.
        page.add_style_tag(content='''
            html,body{background:#fff !important;}
            .deck{padding:0 !important;gap:0 !important;}
            .slide{
              width:100vw !important;max-width:100vw !important;
              height:100vh !important;aspect-ratio:auto !important;
              border-radius:0 !important;box-shadow:none !important;
              page-break-after:always;break-after:page;
            }
            .slide:last-of-type{page-break-after:auto;break-after:auto;}
        ''')

        page.pdf(
            path=str(OUT),
            width=f'{PAGE_W_IN}in',
            height=f'{PAGE_H_IN}in',
            print_background=True,
            margin={'top': '0', 'bottom': '0', 'left': '0', 'right': '0'},
            prefer_css_page_size=False,
        )
        browser.close()
    print('Wrote:', OUT)


if __name__ == '__main__':
    main()
