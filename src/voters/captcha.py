"""Centralised captcha resolution helpers powered by the 2Captcha service."""

import asyncio
import logging
import os

from twocaptcha import TwoCaptcha

logger = logging.getLogger("captcha")


def _get_solver() -> TwoCaptcha:
    api_key = os.environ.get("TWOCAPTCHA_API_KEY", "")
    if not api_key:
        raise ValueError("TWOCAPTCHA_API_KEY non définie dans l'environnement")
    return TwoCaptcha(api_key)


async def solve_recaptcha(page, site_key: str) -> str | None:
    """Resolve a reCAPTCHA v2 challenge via 2Captcha.

    The blocking API call is offloaded to a thread so the event loop is not
    stalled.

    Args:
        page: A Playwright :class:`Page` instance; its ``url`` property is
            used as the data-url sent to 2Captcha.
        site_key: The reCAPTCHA site key (``data-sitekey`` attribute value).

    Returns:
        The solution token string, or ``None`` if the resolution failed.
    """
    try:
        result = await asyncio.to_thread(
            _get_solver().recaptcha, sitekey=site_key, url=page.url
        )
        return result["code"]
    except Exception as exc:  # noqa: BLE001
        logger.error("Échec résolution reCAPTCHA : %s", exc)
        return None


async def solve_hcaptcha(page, site_key: str) -> str | None:
    """Resolve an hCaptcha challenge via 2Captcha.

    The blocking API call is offloaded to a thread so the event loop is not
    stalled.

    Args:
        page: A Playwright :class:`Page` instance; its ``url`` property is
            used as the data-url sent to 2Captcha.
        site_key: The hCaptcha site key (``data-sitekey`` attribute value).

    Returns:
        The solution token string, or ``None`` if the resolution failed.
    """
    try:
        result = await asyncio.to_thread(
            _get_solver().hcaptcha, sitekey=site_key, url=page.url
        )
        return result["code"]
    except Exception as exc:  # noqa: BLE001
        logger.error("Échec résolution hCaptcha : %s", exc)
        return None


async def inject_recaptcha_token(page, token: str) -> None:
    """Inject a reCAPTCHA solution token into the page DOM.

    Sets the value of the hidden ``g-recaptcha-response`` textarea and
    fires the reCAPTCHA callback if the global ``___grecaptcha_cfg``
    configuration object is present.

    Args:
        page: A Playwright :class:`Page` instance.
        token: The solution token returned by :func:`solve_recaptcha`.
    """
    await page.evaluate(
        """(token) => {
            const area = document.getElementById('g-recaptcha-response');
            if (area) {
                area.value = token;
            }
            if (typeof ___grecaptcha_cfg !== 'undefined') {
                const clients = ___grecaptcha_cfg.clients;
                if (clients) {
                    Object.values(clients).forEach((client) => {
                        const callback = Object.values(client).find(
                            (v) => typeof v === 'object' && v !== null && typeof v.callback === 'function'
                        );
                        if (callback) {
                            callback.callback(token);
                        }
                    });
                }
            }
        }""",
        token,
    )
    logger.debug("Token reCAPTCHA injecté")


async def inject_hcaptcha_token(page, token: str) -> None:
    """Inject an hCaptcha solution token into the page DOM.

    Sets the value of the ``textarea[name='h-captcha-response']`` element
    and dispatches a ``change`` event so the surrounding form detects the
    update.

    Args:
        page: A Playwright :class:`Page` instance.
        token: The solution token returned by :func:`solve_hcaptcha`.
    """
    await page.evaluate(
        """(token) => {
            const area = document.querySelector('textarea[name="h-captcha-response"]');
            if (area) {
                area.value = token;
                area.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""",
        token,
    )
    logger.debug("Token hCaptcha injecté")


async def solve_mtcaptcha(page, site_key: str) -> str | None:
    """Resolve an MTCaptcha challenge via 2Captcha.

    The blocking API call is offloaded to a thread so the event loop is not
    stalled.  Resolution typically takes 10–60 seconds.

    Args:
        page: A Playwright :class:`Page` instance; its ``url`` property is
            used as the data-url sent to 2Captcha.
        site_key: The MTCaptcha site key (``data-sitekey`` attribute value).

    Returns:
        The solution token string, or ``None`` if the resolution failed.
    """
    logger.info("Sending MTCaptcha to 2Captcha, waiting for resolution (10-60s)...")
    try:
        result = await asyncio.to_thread(
            _get_solver().mtcaptcha, sitekey=site_key, url=page.url
        )
        logger.info("MTCaptcha solved")
        return result["code"]
    except Exception as exc:  # noqa: BLE001
        logger.error("Échec résolution MTCaptcha : %s", exc)
        return None


async def inject_mtcaptcha_token(page, token: str) -> None:
    """Inject an MTCaptcha solution token into the page DOM.

    Sets the value of ``input[name='mtcaptcha-verifiedtoken']`` and
    dispatches a ``change`` event so the surrounding form detects the update.

    Args:
        page: A Playwright :class:`Page` instance.
        token: The solution token returned by :func:`solve_mtcaptcha`.
    """
    await page.evaluate(
        """(token) => {
            const field = document.querySelector('input[name="mtcaptcha-verifiedtoken"]');
            if (field) {
                field.value = token;
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        }""",
        token,
    )
    logger.debug("MTCaptcha token injected")
