"""
Check if Playwright is installed and working
"""
import sys

print("🔍 Checking Playwright installation...")

try:
    from playwright.sync_api import sync_playwright
    print("✅ Playwright Python package is installed")
except ImportError:
    print("❌ Playwright Python package is NOT installed")
    print("   Run: pip install playwright==1.48.0")
    sys.exit(1)

print("\n🔍 Checking Chromium browser...")
try:
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch(headless=True)
            print("✅ Chromium browser is installed and working")
            browser.close()
        except Exception as e:
            print(f"❌ Chromium browser error: {e}")
            print("   Run: playwright install chromium")
            sys.exit(1)
except Exception as e:
    print(f"❌ Playwright error: {e}")
    sys.exit(1)

print("\n✅ Playwright is ready to use!")
print("   PDF generation should work with Playwright now.")

