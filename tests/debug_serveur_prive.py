"""Debug script — inspects the vote page of serveur-prive.net."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

load_dotenv(_PROJECT_ROOT / ".env")

_URL = "https://serveur-prive.net/minecraft/neodium-2142/vote"
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

        print(f"[→] Navigation vers {_URL}")
        await page.goto(_URL, wait_until="domcontentloaded")
        await page.wait_for_timeout(4000)

        # ── CAPTCHA ───────────────────────────────────────────────────────────
        _sep("CAPTCHA")

        first_img = await page.evaluate("document.querySelector('img')?.src")
        print("Premier img src :", first_img)

        images = await page.evaluate(
            "Array.from(document.querySelectorAll('img'))"
            ".map(i => ({src: i.src, alt: i.alt, class: i.className, id: i.id,"
            " width: i.width, height: i.height}))"
        )
        print("\nToutes les images :")
        for img in images:
            print(" ", img)

        canvases = await page.evaluate(
            "Array.from(document.querySelectorAll('canvas'))"
            ".map(c => ({id: c.id, class: c.className, width: c.width, height: c.height}))"
        )
        print("\nCanvas :")
        for canvas in canvases:
            print(" ", canvas)

        # ── FORM ──────────────────────────────────────────────────────────────
        _sep("FORM")

        forms = await page.evaluate(
            "Array.from(document.querySelectorAll('form'))"
            ".map(f => ({id: f.id, action: f.action, html: f.outerHTML.slice(0, 600)}))"
        )
        print("Formulaires :")
        for form in forms:
            print(" ", form)

        inputs = await page.evaluate(
            "Array.from(document.querySelectorAll('input'))"
            ".map(i => ({type: i.type, name: i.name, id: i.id,"
            " placeholder: i.placeholder, class: i.className.slice(0,60)}))"
        )
        print("\nInputs :")
        for inp in inputs:
            print(" ", inp)

        buttons = await page.evaluate(
            "Array.from(document.querySelectorAll('button, input[type=submit]'))"
            ".map(b => ({tag: b.tagName, text: b.innerText?.trim(), id: b.id,"
            " value: b.value, class: b.className.slice(0,60)}))"
        )
        print("\nBoutons :")
        for btn in buttons:
            print(" ", btn)

        # ── IFRAMES ───────────────────────────────────────────────────────────
        _sep("IFRAMES")

        iframes = await page.evaluate(
            "Array.from(document.querySelectorAll('iframe'))"
            ".map(f => ({src: f.src, id: f.id, class: f.className}))"
        )
        for frame in iframes:
            print(" ", frame)

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
