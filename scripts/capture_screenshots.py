"""Capture UI screenshots of the running Streamlit app into docs/.

Requires the app to be serving (default http://127.0.0.1:8533) and Playwright Chromium
installed (`python -m playwright install chromium`). Run:

    python -m scripts.capture_screenshots
"""
from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8533"
DOCS = Path(__file__).resolve().parent.parent / "docs"


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 1000})
        page.goto(URL, wait_until="networkidle")

        # Wait for the app shell.
        page.get_by_role("heading", name="Smart Code Reviewer").first.wait_for(timeout=30000)

        # --- Review tab: run the review on the pre-filled sample, then screenshot. ---
        page.get_by_role("button", name="Run review").click()
        # The pipeline makes three model calls; wait for the positive note to appear.
        page.get_by_text("Positive note", exact=False).first.wait_for(timeout=90000)
        page.wait_for_timeout(1200)  # let scores/expanders settle
        page.screenshot(path=str(DOCS / "ui_review.png"), full_page=True)
        print("wrote", DOCS / "ui_review.png")

        # --- Eval tab: render the harness report, then screenshot. ---
        page.get_by_role("tab", name="Eval harness").click()
        page.get_by_text("Eval Report", exact=False).first.wait_for(timeout=30000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(DOCS / "ui_eval.png"), full_page=True)
        print("wrote", DOCS / "ui_eval.png")

        browser.close()


if __name__ == "__main__":
    main()
