"""Voter implementation for serveur-prive.net."""

import asyncio

from .base import BaseVoter
from .captcha import inject_mtcaptcha_token, solve_mtcaptcha


class ServeurPriveVoter(BaseVoter):
    """Votes on serveur-prive.net using MTCaptcha."""

    SITEKEY = "MTPublic-42pXmytZe"

    async def vote(self, page) -> bool:
        """Execute the full vote sequence for serveur-prive.net.

        Args:
            page: A Playwright :class:`Page` instance.

        Returns:
            ``True`` if the vote was submitted, ``False`` if a step failed.
        """
        try:
            # 1. Navigation
            self.logger.info("Navigation vers %s", self.url)
            await page.goto(self.url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(3000)
            await page.wait_for_selector("input#username", timeout=20000)

            # 2. Remplir le pseudo
            await page.locator("input#username").fill(self.pseudo)
            self.logger.info("Pseudo filled")

            # 3. Résolution MTCaptcha
            self.logger.info("Résolution MTCaptcha (sitekey=%s)", self.SITEKEY)
            token = await solve_mtcaptcha(page, self.SITEKEY)
            if token is None:
                self.logger.warning("MTCaptcha non résolu")
                return False

            # 4. Injection du token
            await inject_mtcaptcha_token(page, token)
            await page.wait_for_timeout(1000)

            # 5. Clic sur le bouton de vote
            await page.locator("button#voteBtn").click()
            self.logger.info("Vote button clicked")

            # 6. Attente résultat
            await asyncio.sleep(4)

            # 7. Log confirmation
            title = await page.title()
            self.logger.info("Titre : %s | URL : %s", title, page.url)
            return True

        except Exception as exc:  # noqa: BLE001
            self.logger.error("Erreur lors du vote : %s", exc)
            return False
