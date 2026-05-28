# -*- coding: utf-8 -*-
"""Voter implementation for liste-serveurs-minecraft.org."""

import asyncio

from .base import BaseVoter
from .captcha import solve_recaptcha

_CONSENT_SELECTOR = (
    "button.fc-button.fc-vendor-preferences-accept-all, "
    "button:has-text('Tout accepter'), "
    "button:has-text('Autoriser')"
)

_FETCH_VOTE_JS = """\
async (args) => {
    const response = await fetch(args.url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: 'g_recaptcha_response=' + encodeURIComponent(args.token)
    });
    return await response.text();
}
"""


class LsmVoter(BaseVoter):
    """Votes on liste-serveurs-minecraft.org via a direct POST after reCAPTCHA resolution."""

    SITEKEY = "6Lc1bYIUAAAAAD867UqRvUnwjq9cX2tLz7cE3oGo"
    VERIF_URL = (
        "https://www.liste-serveurs-minecraft.org"
        "/wp-content/themes/DL/captchavote/verif_votes.php"
    )

    async def vote(self, page) -> bool:
        """Execute the vote sequence for liste-serveurs-minecraft.org.

        Navigates to the vote page, solves the invisible reCAPTCHA, then
        submits the token directly via a fetch() POST call.  No button click
        is required.

        Args:
            page: A Playwright :class:`Page` instance.

        Returns:
            ``True`` if the server confirms the vote, ``False`` otherwise.
        """
        vote_url = (
            f"https://www.liste-serveurs-minecraft.org/vote/"
            f"?idc=202832&nickname={self.pseudo}"
        )
        try:
            # 1. Navigation
            self.logger.info("Navigation vers %s", vote_url)
            await page.goto(vote_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(3000)

            # 2. Fermer modale consentement
            try:
                await page.wait_for_selector(_CONSENT_SELECTOR, timeout=5000)
                await page.locator(_CONSENT_SELECTOR).first.click()
                await asyncio.sleep(2)
                self.logger.info("Modale consentement ferm\u00e9e")
            except Exception:
                self.logger.debug("Pas de modale consentement")

            # 3. R\u00e9solution reCAPTCHA invisible
            self.logger.info("R\u00e9solution reCAPTCHA (sitekey=%s)", self.SITEKEY)
            token = await solve_recaptcha(page, self.SITEKEY)
            if token is None:
                self.logger.warning("Captcha reCAPTCHA non r\u00e9solu")
                return False

            # 4. Soumission du vote via fetch() dans le contexte de la page
            self.logger.info("Soumission du vote via POST vers %s", self.VERIF_URL)
            response_text = await page.evaluate(
                _FETCH_VOTE_JS,
                {"url": self.VERIF_URL, "token": token},
            )

            # 5. Analyse de la r\u00e9ponse
            self.logger.info("verif_votes response: %s", response_text)
            if "display_button" in (response_text or ""):
                self.logger.info("Vote confirmed by server")
                return True
            else:
                self.logger.warning("Unexpected response: %s", response_text)
                return False

        except Exception as exc:
            self.logger.error("Erreur lors du vote : %s", exc)
            return False
