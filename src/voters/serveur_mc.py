"""Voter implementation for serveur-minecraft.com."""

import asyncio

from .base import BaseVoter
from .captcha import (
    inject_hcaptcha_token,
    inject_recaptcha_token,
    solve_hcaptcha,
    solve_recaptcha,
)

_PSEUDO_SELECTORS = [
    "input[name='pseudo']",
    "input[name='username']",
    "input[placeholder*='seudo']",
]

_BUTTON_SELECTOR = "button[type='submit'], input[type='submit'], .vote-button"


class ServeurMcVoter(BaseVoter):
    """Votes on serveur-minecraft.com, filling the pseudo field when present."""

    async def vote(self, page) -> bool:
        """Navigate to the vote page, optionally fill the pseudo, then submit.

        Args:
            page: A Playwright :class:`Page` instance.

        Returns:
            ``True`` if the vote was submitted successfully, ``False`` otherwise.
        """
        try:
            self.logger.info("Navigation vers %s", self.url)
            await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)

            for selector in _PSEUDO_SELECTORS:
                field = page.locator(selector).first
                if await field.count() > 0:
                    self.logger.debug("Champ pseudo trouvé : %s", selector)
                    await field.fill(self.pseudo)
                    break
            else:
                self.logger.debug("Aucun champ pseudo détecté")

            if await page.locator("div.g-recaptcha, iframe[src*='recaptcha']").count() > 0:
                site_key = await page.get_attribute("div.g-recaptcha", "data-sitekey")
                token = await solve_recaptcha(page, site_key)
                if token is None:
                    self.logger.warning("Captcha reCAPTCHA non résolu")
                    return False
                await inject_recaptcha_token(page, token)

            if await page.locator("div.h-captcha, iframe[src*='hcaptcha']").count() > 0:
                site_key = await page.get_attribute("div.h-captcha", "data-sitekey")
                token = await solve_hcaptcha(page, site_key)
                if token is None:
                    self.logger.warning("Captcha hCaptcha non résolu")
                    return False
                await inject_hcaptcha_token(page, token)

            button = page.locator(_BUTTON_SELECTOR).first
            await button.click()
            self.logger.info("Vote soumis")

            await asyncio.sleep(3)
            return True
        except Exception as exc:  # noqa: BLE001
            self.logger.error("Erreur lors du vote : %s", exc)
            return False
