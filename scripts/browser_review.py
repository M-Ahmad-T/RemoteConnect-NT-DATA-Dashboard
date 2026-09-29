"""Capture all six live pages in Chrome; run against a local Streamlit server."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", default="after")
    parser.add_argument("--url", default="http://127.0.0.1:8501")
    args = parser.parse_args()
    output = ROOT / "artifacts" / args.phase
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        for width, height, label in [(1440, 1000, "desktop"), (390, 844, "mobile")]:
            context = browser.new_context(viewport={"width": width, "height": height}, device_scale_factor=1)
            page = context.new_page()
            page.goto(args.url)
            page.locator("h1").first.wait_for(timeout=60000)
            page.wait_for_timeout(2000)
            page.locator('[data-testid="stSidebarNav"] a').first.wait_for(state="attached")
            links = page.locator('[data-testid="stSidebarNav"] a').evaluate_all("els => els.map(e => ({url:e.href, title:e.innerText}))")
            assert len(links) == 6, links
            for i, link in enumerate(links):
                errors = []
                def on_error(error):
                    errors.append(str(error))
                page.on("pageerror", on_error)
                page.goto(link["url"])
                page.locator("h1").first.wait_for(timeout=60000)
                page.wait_for_timeout(7000)
                # Close navigation on narrow screens so the actual page is visible.
                if label == "mobile":
                    close = page.locator('[data-testid="stSidebarCollapseButton"] button')
                    if close.count() and close.is_visible() and close.bounding_box()["x"] >= 0:
                        close.click()
                        page.wait_for_timeout(400)
                page.screenshot(path=str(output / f"{i+1}-{label}.png"), full_page=True)
                if i in (2, 4):
                    page.locator('[data-testid="stMain"]').evaluate("el => el.scrollTop = (el.scrollHeight - el.clientHeight) / 2")
                    page.wait_for_timeout(300)
                    page.screenshot(path=str(output / f"{i+1}-{label}-middle.png"), full_page=True)
                page.locator('[data-testid="stMain"]').evaluate("el => el.scrollTop = el.scrollHeight")
                page.wait_for_timeout(500)
                page.screenshot(path=str(output / f"{i+1}-{label}-bottom.png"), full_page=True)
                text = page.locator('[data-testid="stMain"]').inner_text()
                (output / f"{i+1}-{label}.txt").write_text(text, encoding="utf-8")
                results.append({"page": link["title"], "viewport": label,
                                "heading": page.locator("h1").first.inner_text(),
                                "exceptions": page.locator('[data-testid="stException"]').all_text_contents(),
                                "browser_errors": errors,
                                "overflow": page.evaluate("document.documentElement.scrollWidth > innerWidth")})
                page.remove_listener("pageerror", on_error)
                assert results[-1]["heading"] == link["title"], results[-1]
                assert not results[-1]["exceptions"] and not errors and not results[-1]["overflow"], results[-1]
            context.close()
        browser.close()
    (output / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
