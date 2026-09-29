"""Exercise real Streamlit navigation, controls, map and downloads in Chrome."""
import json
from pathlib import Path

import pandas as pd
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/interactions"


def settle(page):
    page.wait_for_timeout(1000)
    expect(page.locator('[data-testid="stException"]')).to_have_count(0)


def choose(page, label, value):
    combo = page.locator('[data-testid="stSelectbox"]').filter(has_text=label).get_by_role("combobox")
    combo.click()
    combo.fill(value)
    page.get_by_role("option", name=value, exact=True).click()
    settle(page)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    checks = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width":1440, "height":1000}, accept_downloads=True)
        page = context.new_page()
        external = []
        page.on("request", lambda request: external.append(request.url) if not request.url.startswith(("http://127.0.0.1", "ws://127.0.0.1", "data:")) else None)
        page.goto("http://127.0.0.1:8501")
        expect(page.get_by_role("heading", name="Overview", exact=True)).to_be_visible(timeout=60000)
        settle(page)
        sidebar = page.locator('[data-testid="stSidebar"]')
        page.get_by_role("button", name="Explore this location", exact=True).click()
        expect(page.get_by_role("heading", name="Ngayawilli", exact=True)).to_be_visible()
        checks.append("Overview featured action opens Ngayawilli")
        sidebar.get_by_text("Filter source locations", exact=True).click()
        choose(page, "NT source coverage flag", "Multiple flags")
        expect(sidebar.get_by_text("7 of 188 source records", exact=True)).to_be_visible()
        choose(page, "Choose a source location", "Mount Ebenezer · Small cell + Proximity to cell")
        expect(page.get_by_role("heading", name="Mount Ebenezer", exact=True)).to_be_visible()
        checks.append("Coverage filter preserves multiple flags and Explorer honours filtered selection")
        sidebar.get_by_role("link", name="Save snapshots", exact=True).click()
        expect(page.get_by_role("heading", name="Save snapshots", exact=True)).to_be_visible()
        expect(sidebar.get_by_text("7 of 188 source records", exact=True)).to_be_visible()
        expect(page.locator('[data-testid="stMain"]')).to_contain_text("Mount Ebenezer")
        for label, filename in [("Save readable location snapshot", "location.txt"), ("Save location CSV", "location.csv"), ("Save filtered CSV", "filtered.csv")]:
            with page.expect_download() as download:
                page.get_by_role("button", name=label, exact=True).click()
            download.value.save_as(OUT / filename)
        one = pd.read_csv(OUT / "location.csv")
        many = pd.read_csv(OUT / "filtered.csv")
        assert one.loc[0,"community"] == "MOUNT EBENEZER"
        assert one.loc[0,"coverage_type"] == "Small cell + Proximity to cell"
        assert len(many) == 7
        assert (many.coverage_flag_count == 2).all()
        assert "Distinct mapped site keys within 50 km" in (OUT / "location.txt").read_text(encoding="utf-8")
        checks.append("Three actual downloads saved and parsed; selection and 7-row filter persist across navigation")

        sidebar.get_by_role("link", name="Connectivity map", exact=True).click()
        expect(page.get_by_role("heading", name="Connectivity map", exact=True)).to_be_visible()
        page.get_by_text("Overlay ACCC operator sites", exact=True).click()
        expect(page.locator('[data-testid="stMain"]')).to_contain_text("All 419 NT operator-site records")
        page.wait_for_function("Array.from(document.querySelectorAll('.js-plotly-plot')).some(e => e.data && e.data.some(t => t.name === 'Telstra sites'))")
        # Exercise rendered marker hover, then preserve the overlay screenshot.
        page.locator(".scatterlayer .trace .point").first.hover(force=True)
        page.screenshot(path=str(OUT / "map-overlay.png"))
        checks.append("Map overlay renders full NT operator records alongside filtered circles")

        sidebar.get_by_role("link", name="Data insights", exact=True).click()
        expect(page.get_by_role("heading", name="Data insights", exact=True)).to_be_visible()
        sidebar.get_by_text("Adjust the indicator", exact=True).click()
        sliders = sidebar.get_by_role("slider")
        expect(sliders).to_have_count(4)
        expect(sliders.nth(3)).to_be_disabled()
        sliders.nth(0).focus()
        sliders.nth(0).press("End")
        settle(page)
        expect(sidebar).to_contain_text("coverage 71.4286%")
        expect(page.locator('[data-testid="stMain"]')).not_to_contain_text("0 of 7 scored records change")
        page.locator('[data-testid="stMain"]').evaluate("el => el.scrollTop = el.scrollHeight")
        page.screenshot(path=str(OUT / "score-sensitivity.png"))
        checks.append("Coverage slider changes effective weights and sensitivity; missing context control disabled")

        choose(page, "Band at a site within 50 km", "Not assessed")
        expect(sidebar.get_by_text("0 of 188 source records", exact=True)).to_be_visible()
        sidebar.get_by_role("link", name="Community explorer", exact=True).click()
        expect(page.locator('[data-testid="stMain"]')).to_contain_text("No source locations match")
        sidebar.get_by_role("link", name="Save snapshots", exact=True).click()
        expect(page.locator('[data-testid="stMain"]')).to_contain_text("No source locations match")
        expect(page.locator('[data-testid="stDownloadButton"]')).to_have_count(0)
        checks.append("Empty filtered Explorer and Downloads do not fall back to unfiltered records")
        sidebar.get_by_role("link", name="Digital inclusion", exact=True).click()
        expect(page.locator('[data-testid="stMain"]')).to_contain_text("No matched digital inclusion observations")
        checks.append("ADII missing-data state remains explicit")
        assert not external, external
        checks.append("No external network requests during app navigation and map interactions")
        context.close()

        mobile = browser.new_context(viewport={"width":390, "height":844}, is_mobile=True, has_touch=True)
        page = mobile.new_page()
        page.goto("http://127.0.0.1:8501")
        expect(page.get_by_role("heading", name="Overview", exact=True)).to_be_visible(timeout=60000)
        settle(page)
        page.locator('[data-testid="stExpandSidebarButton"]').click()
        sidebar = page.locator('[data-testid="stSidebar"]')
        sidebar.get_by_role("link", name="Community explorer", exact=True).click()
        expect(page.get_by_role("heading", name="Community explorer", exact=True)).to_be_visible()
        close = page.locator('[data-testid="stSidebarCollapseButton"] button')
        if close.count() and close.bounding_box()["x"] >= 0:
            close.click()
        choose(page, "Choose a source location", "Mutitjulu · Macro cell + Proximity to cell")
        expect(page.get_by_role("heading", name="Mutitjulu", exact=True)).to_be_visible()
        assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
        page.screenshot(path=str(OUT / "mobile-profile.png"))
        checks.append("390px touch layout: sidebar navigation and location selection work without page overflow")
        mobile.close()
        browser.close()
    (OUT / "results.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))


if __name__ == "__main__":
    main()
