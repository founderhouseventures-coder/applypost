import os
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = ROOT / "docs" / "saas-preview"
BASE_URL = os.environ.get("JOBMAIL_BASE_URL", "http://127.0.0.1:8000")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(
            viewport={"width": 1440, "height": 1000},
            device_scale_factor=1,
            accept_downloads=True,
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
        assert page.get_by_label("Username").is_visible()
        assert page.get_by_label("Email:").is_visible()
        updates = page.locator('input[name="product_updates"]')
        update_count = updates.count()
        assert update_count == 1, (
            f"Expected one product-update opt-in, found {update_count} at {page.url}"
        )
        assert updates.is_visible()
        assert not updates.is_checked()
        page.screenshot(path=str(OUTPUT / "signup-desktop.png"), full_page=True)
        page.get_by_role("link", name="Back to sign in").click()
        assert page.get_by_role("link", name="Forgot password?").is_visible()

        username = os.environ.get("JOBMAIL_QA_USERNAME")
        password = os.environ.get("JOBMAIL_QA_PASSWORD")
        if username and password:
            page.goto(f"{BASE_URL}/accounts/login/", wait_until="networkidle")
            page.locator('input[name="username"]').fill(username)
            page.locator('input[name="password"]').fill(password)
            page.get_by_role("button", name="Sign in").click()
            assert page.get_by_role(
                "heading", name=f"Good to see you, {username}."
            ).is_visible()
            assert page.get_by_text("27 tracked").is_visible()
            page.screenshot(path=str(OUTPUT / "dashboard-desktop.png"), full_page=True)

            page.get_by_label("Search company, role, or source").fill("Company 26")
            page.get_by_role("button", name="Filter").click()
            assert page.get_by_text("1 shown · 27 tracked").is_visible()
            assert page.get_by_text("Company 26").is_visible()
            page.get_by_role("link", name="Clear").click()
            page.get_by_label("Follow-up").select_option("due")
            page.get_by_role("button", name="Filter").click()
            assert page.get_by_text("1 shown · 27 tracked").is_visible()
            assert page.get_by_text("Company 26").is_visible()
            page.get_by_role("link", name="Clear").click()

            pages = page.get_by_role("navigation", name="Applications pages")
            pages.get_by_role("link", name="Next").click()
            assert page.get_by_text("Page 2 of 2").is_visible()

            page.get_by_label("Company:").fill("QA Launch")
            page.get_by_label("Role:").fill("Product Engineer")
            page.get_by_label("Notes:").fill("Synthetic browser QA")
            assert page.get_by_label("Notes:").get_attribute("maxlength") == "1000"
            page.get_by_role("button", name="Save application").click()
            assert page.get_by_text("QA Launch").is_visible()
            assert page.get_by_text("28 tracked").is_visible()
            application = page.locator(".application-row").filter(has_text="QA Launch")
            application.get_by_role("link", name="Edit").click()
            assert page.get_by_role("heading", name="Update application").is_visible()
            page.get_by_label("Company:").fill("QA Launch Updated")
            page.get_by_role("button", name="Save changes").click()
            assert page.get_by_text("QA Launch Updated").is_visible()
            with page.expect_download() as download_info:
                page.locator('a[href="/export/"]').click()
            export = download_info.value
            assert export.suggested_filename == "jobmail-applications.csv"
            export_text = Path(export.path()).read_text(encoding="utf-8")
            assert "QA Launch Updated" in export_text
            page.get_by_role(
                "button", name="Delete Product Engineer at QA Launch Updated"
            ).click()
            assert not page.get_by_text("QA Launch Updated").count()
            page.get_by_role("link", name="Import CSV").click()
            page.locator("#csv-file").set_input_files(
                {
                    "name": "browser-import.csv",
                    "mimeType": "text/csv",
                    "buffer": (
                        b"Company,Role,Status,Source,Job URL,Applied on,"
                        b"Follow-up,Notes\n"
                        b"Import QA,Analyst,Applied,,,,,Synthetic browser import\n"
                    ),
                }
            )
            page.get_by_role("button", name="Preview import").click()
            assert page.get_by_text(
                "1 valid row · 0 duplicates or rows with errors", exact=True
            ).is_visible()
            page.screenshot(
                path=str(OUTPUT / "import-preview-desktop.png"), full_page=True
            )
            page.set_viewport_size({"width": 390, "height": 844})
            assert page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            ), "Import preview has horizontal page overflow at 390px"
            page.screenshot(
                path=str(OUTPUT / "import-preview-mobile.png"), full_page=True
            )
            page.set_viewport_size({"width": 1440, "height": 1000})
            page.get_by_role("button", name="Import 1 valid row").click()
            assert page.get_by_text("28 tracked").is_visible()
            page.set_viewport_size({"width": 390, "height": 844})
            page.screenshot(path=str(OUTPUT / "dashboard-mobile.png"), full_page=True)
            layout = page.evaluate(
                "document.documentElement.scrollWidth <= window.innerWidth"
            )
            assert layout, "Dashboard has horizontal page overflow at 390px"

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
