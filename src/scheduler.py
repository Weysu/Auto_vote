"""Scheduler — orchestrates vote jobs using APScheduler DateTrigger (one-shot)."""

import logging
import random
from datetime import datetime, timedelta

import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from playwright.async_api import async_playwright

from voters.base import BaseVoter
from voters.lsm import LsmVoter
from voters.serveur_mc import ServeurMcVoter
from voters.serveur_prive import ServeurPriveVoter

logger = logging.getLogger("scheduler")

_TZ = pytz.timezone("Europe/Paris")
_WINDOW_START = (7, 30)   # 07:30
_WINDOW_END   = (0, 30)   # 00:30 (next day boundary)
_JITTER_MAX   = 900       # seconds

_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)

_VOTER_CLASSES: dict[str, type[BaseVoter]] = {
    "lsm": LsmVoter,
    "serveur_prive": ServeurPriveVoter,
    "serveur_mc": ServeurMcVoter,
}


def _apply_window(dt: datetime) -> datetime:
    """Adjust *dt* (Paris-aware) so it falls inside the active window.

    Active window spans midnight: 07:30–23:59 and 00:00–00:30.
    Outside window: 00:31–07:29 → push to 07:30 same calendar day.
    """
    h, m = dt.hour, dt.minute
    start_minutes = _WINDOW_START[0] * 60 + _WINDOW_START[1]  # 450
    end_minutes   = _WINDOW_END[0]   * 60 + _WINDOW_END[1]    # 30
    current_minutes = h * 60 + m

    # Outside window: 00:31 ≤ time ≤ 07:29
    if end_minutes < current_minutes < start_minutes:
        adjusted = dt.replace(hour=_WINDOW_START[0], minute=_WINDOW_START[1], second=0, microsecond=0)
        logger.debug("_apply_window: %s → %s (hors fenêtre, avancé à 07:30)", dt, adjusted)
        return adjusted

    logger.debug("_apply_window: %s → inchangé (dans la fenêtre)", dt)
    return dt  # inside window (07:30–23:59 or 00:00–00:30)


def _next_run_dt(interval_hours: float) -> datetime:
    """Return the next Paris-aware datetime to run, with jitter applied and
    window enforcement.
    """
    jitter = random.randint(0, _JITTER_MAX)
    delta = timedelta(hours=float(interval_hours), seconds=jitter)
    now = datetime.now(_TZ)
    candidate = now + delta
    return _apply_window(candidate)


async def run_vote(
    voter: BaseVoter,
    scheduler: AsyncIOScheduler,
    site_config: dict,
    headless: bool = True,
) -> None:
    """Execute a single vote, then schedule the next one-shot run."""
    name = site_config["name"]
    interval_hours = site_config["interval_hours"]

    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        try:
            context = await browser.new_context(user_agent=_USER_AGENT)
            page = await context.new_page()
            success = await voter.vote(page)
            if success:
                logger.info("[%s] Vote réussi", name)
            else:
                logger.warning("[%s] Vote échoué", name)
        finally:
            await browser.close()

    # Schedule the next one-shot run
    next_run = _next_run_dt(interval_hours)
    scheduler.add_job(
        run_vote,
        trigger=DateTrigger(run_date=next_run),
        args=[voter, scheduler, site_config],
        kwargs={"headless": headless},
        id=name,
        name=f"vote_{name}",
        replace_existing=True,
    )
    logger.info("Prochain vote pour %s prévu à %s (heure Paris)", name, next_run.strftime("%Y-%m-%d %H:%M:%S %Z"))


def setup_scheduler(config: dict) -> AsyncIOScheduler:
    """Build and return an AsyncIOScheduler with one-shot DateTrigger jobs.

    Each site gets an immediate first run (now + 5 s), then self-reschedules
    after every execution.

    Args:
        config: Parsed content of ``config.yaml``.
            Expected keys: ``pseudo`` (str), ``sites`` (list of dicts
            with ``name``, ``url``, ``interval_hours``).

    Returns:
        A configured (but not yet started) :class:`AsyncIOScheduler`.
    """
    pseudo = config["pseudo"]
    scheduler = AsyncIOScheduler(timezone=_TZ)

    for site in config.get("sites", []):
        name = site["name"]
        url  = site["url"]

        if not site.get("enabled", True):
            logger.info("Site %s disabled, skipping", name)
            continue

        voter_class = _VOTER_CLASSES.get(name)
        if voter_class is None:
            logger.warning("Site inconnu ignoré : %s", name)
            continue

        voter = voter_class(pseudo=pseudo, url=url)
        first_run = datetime.now(_TZ) + timedelta(seconds=5)

        scheduler.add_job(
            run_vote,
            trigger=DateTrigger(run_date=first_run),
            args=[voter, scheduler, site],
            id=name,
            name=f"vote_{name}",
            replace_existing=True,
        )
        logger.info(
            "Premier vote pour %s prévu à %s (heure Paris)",
            name,
            first_run.strftime("%Y-%m-%d %H:%M:%S %Z"),
        )

    return scheduler
