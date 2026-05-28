"""Debug script — inspects the Neodium server page on LSM to locate vote links."""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from playwright.async_api import async_playwright

_PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

load_dotenv(_PROJECT_ROOT / ".env")

_URL = "https://www.liste-serveurs-minecraft.org/serveur-minecraft/neodium-2/"
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
        await page.goto(_URL, wait_until="networkidle")
        await asyncio.sleep(2)

        # ── BOUTONS ───────────────────────────────────────────────────────────
        _sep("BOUTONS")
        buttons = await page.evaluate(
            "Array.from(document.querySelectorAll('button, input[type=submit], a'))"
            ".map(b => ({tag: b.tagName, text: b.innerText?.trim().slice(0,50),"
            " href: b.href, id: b.id, class: b.className?.slice(0,60)}))"
        )
        for b in buttons:
            print(" ", b)

        # ── LIEN VOTE ─────────────────────────────────────────────────────────
        _sep("LIEN VOTE")
        vote_links = await page.evaluate(
            "Array.from(document.querySelectorAll('a[href*=\"vote\"], a[href*=\"voter\"]'))"
            ".map(a => ({text: a.innerText?.trim(), href: a.href}))"
        )
        for link in vote_links:
            print(" ", link)

        # ── FORMULAIRES ───────────────────────────────────────────────────────
        _sep("FORMULAIRES")
        forms = await page.evaluate(
            "Array.from(document.querySelectorAll('form'))"
            ".map(f => ({id: f.id, action: f.action, html: f.outerHTML.slice(0,300)}))"
        )
        for form in forms:
            print(" ", form)

        # ── Inspection manuelle ───────────────────────────────────────────────
        _sep("INSPECTION MANUELLE")
        print("Navigateur ouvert 30s pour inspection manuelle…")
        await asyncio.sleep(30)

        await browser.close()
        print("\n[✓] Navigateur fermé.")


if __name__ == "__main__":
    asyncio.run(main())
