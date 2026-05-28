"""Entry point — loads configuration and starts the vote scheduler."""

import asyncio
import logging
import os

import yaml
from dotenv import load_dotenv

from scheduler import setup_scheduler


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _load_config() -> dict:
    """Load config.yaml and inject MINECRAFT_PSEUDO from the environment."""
    with open("config.yaml", encoding="utf-8") as fh:
        config = yaml.safe_load(fh)

    pseudo = os.environ.get("MINECRAFT_PSEUDO", "")
    if not pseudo:
        logging.getLogger("main").warning(
            "MINECRAFT_PSEUDO est vide — vérifiez votre fichier .env"
        )
    config["pseudo"] = pseudo
    return config


async def _run() -> None:
    log = logging.getLogger("main")
    config = _load_config()
    scheduler = setup_scheduler(config)
    scheduler.start()
    log.info("Scheduler démarré — en attente des jobs")
    try:
        await asyncio.Event().wait()
    except (KeyboardInterrupt, SystemExit):
        log.info("Arrêt demandé")
    finally:
        scheduler.shutdown()
        log.info("Scheduler arrêté")


if __name__ == "__main__":
    load_dotenv()
    _configure_logging()
    asyncio.run(_run())
