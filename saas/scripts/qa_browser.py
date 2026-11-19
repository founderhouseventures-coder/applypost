from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "saas-preview"
BASE_URL = "http://127.0.0.1:8000"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000}, device_scale_factor=1
        )
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        response = page.goto(BASE_URL, wait_until="networkidle")
        assert response and response.status == 200
        assert page.get_by_role(
            "heading", name="Keep every opportunity moving forward."
        ).is_visible()
        assert page.get_by_role("link", name="Start your tracker").is_visible()
        assert page.locator('link[rel="canonical"]').count() == 1
        page.screenshot(path=str(OUTPUT / "landing-desktop.png"), full_page=True)

        page.get_by_role("link", name="Start your tracker").click()
        assert page.get_by_role("heading", name="Create your account").is_visible()
        page.screenshot(path=str(OUTPUT / "signup-desktop.png"), full_page=True)

        page.set_viewport_size({"width": 390, "height": 844})
        page.goto(BASE_URL, wait_until="networkidle")
        assert page.evaluate(
            "document.documentElement.scrollWidth <= window.innerWidth"
        )
        assert page.get_by_role("link", name="Start your tracker").is_visible()
        page.screenshot(path=str(OUTPUT / "landing-mobile.png"), full_page=True)
        assert not errors, errors
        browser.close()
    print(f"Browser checks passed; screenshots: {OUTPUT}")


if __name__ == "__main__":
    main()
