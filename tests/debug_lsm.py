"""Debug script — inspects the LSM vote page and dumps reCAPTCHA/form info."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

load_dotenv(_PROJECT_ROOT / ".env")

_URL = "https://www.liste-serveurs-minecraft.org/vote/?idc=202832&nickname=W3ysu"
_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


def _sep(title: str) -> None:
    print(f"\n{'─' * 10} {title} {'─' * 10}")


async def main() -> None:
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=False)
        context = await browser.new_context(user_agent=_USER_AGENT)
        page = await context.new_page()

        # ── 1. Navigation ─────────────────────────────────────────────────────
        print(f"[→] Navigation vers {_URL}")
        await page.goto(_URL, wait_until="networkidle")

        # ── 2. Modale RGPD ────────────────────────────────────────────────────
        rgpd_btn = page.locator("button:has-text('Autoriser')").first
        if await rgpd_btn.count() > 0:
            print("[✓] Modale RGPD trouvée — fermeture")
            await rgpd_btn.click()
            await asyncio.sleep(2)
        else:
            print("[–] Pas de modale RGPD")

        # ── 3. Attente chargement reCAPTCHA ───────────────────────────────────
        print("[…] Attente 3s pour le chargement du reCAPTCHA")
        await asyncio.sleep(3)

        # ── RECAPTCHA ─────────────────────────────────────────────────────────
        _sep("RECAPTCHA")

        outer_html = await page.evaluate(
            "document.querySelector('div.g-recaptcha')?.outerHTML"
        )
        print("div.g-recaptcha outerHTML :", outer_html)

        sitekey = await page.evaluate(
            "document.querySelector('div.g-recaptcha')?.dataset?.sitekey"
        )
        print("data-sitekey              :", sitekey)

        iframe_src = await page.evaluate(
            "document.querySelector('iframe[src*=\"recaptcha\"]')?.src"
        )
        print("iframe src                :", iframe_src)

        cfg_keys = await page.evaluate(
            "Object.keys(window.___grecaptcha_cfg?.clients || {})"
        )
        print("___grecaptcha_cfg keys    :", cfg_keys)

        cfg_json = await page.evaluate(
            "JSON.stringify(window.___grecaptcha_cfg?.clients)"
        )
        truncated = (cfg_json or "")[:500]
        print("___grecaptcha_cfg.clients :", truncated, "…" if len(cfg_json or "") > 500 else "")

        # ── FORMULAIRE ────────────────────────────────────────────────────────
        _sep("FORMULAIRE")

        form_html = await page.evaluate("document.querySelector('form')?.outerHTML")
        truncated_form = (form_html or "")[:1000]
        print("form outerHTML :", truncated_form, "…" if len(form_html or "") > 1000 else "")

        inputs = await page.evaluate(
            "Array.from(document.querySelectorAll('input')).map(i => "
            "({type: i.type, name: i.name, id: i.id, value: i.value}))"
        )
        print("\nInputs :")
        for inp in inputs:
            print(" ", inp)

        buttons = await page.evaluate(
            "Array.from(document.querySelectorAll('button, input[type=submit]')).map(b => "
            "({tag: b.tagName, type: b.type, text: b.innerText, id: b.id, class: b.className}))"
        )
        print("\nBoutons :")
        for btn in buttons:
            print(" ", btn)

        # ── PAGE ──────────────────────────────────────────────────────────────
        _sep("PAGE")

        title = await page.title()
        print("Titre   :", title)
        print("URL     :", page.url)

        cookies = await page.evaluate("document.cookie")
        print("Cookies :", cookies)

        # ── Inspection manuelle ───────────────────────────────────────────────
        _sep("INSPECTION MANUELLE")
        print("Navigateur ouvert 30s pour inspection manuelle…")
        await asyncio.sleep(30)

        await browser.close()
        print("\n[✓] Navigateur fermé.")


if __name__ == "__main__":
    asyncio.run(main())
