"""Smoke test — runs each voter manually with a visible browser window."""

import argparse
import asyncio
import logging
import os
import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).parent.parent

# Allow imports from src/ when running from the project root.
sys.path.insert(0, str(_PROJECT_ROOT / "src"))

import yaml
from dotenv import load_dotenv

from scheduler import run_vote
from voters.lsm import LsmVoter
from voters.serveur_mc import ServeurMcVoter
from voters.serveur_prive import ServeurPriveVoter

_VOTER_CLASSES = {
    "lsm": LsmVoter,
    "serveur_prive": ServeurPriveVoter,
    "serveur_mc": ServeurMcVoter,
}


def _configure_logging() -> None:
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    )


def _load_config() -> dict:
    config_path = _PROJECT_ROOT / "config.yaml"
    with open(config_path, encoding="utf-8") as fh:
        config = yaml.safe_load(fh)
    config["pseudo"] = os.environ.get("MINECRAFT_PSEUDO", "")
    return config


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Smoke test — lance un vote visible pour un ou tous les sites."
    )
    parser.add_argument(
        "--site",
        choices=[*_VOTER_CLASSES.keys(), "all"],
        default="all",
        help="Site à tester (défaut : all).",
    )
    return parser.parse_args()


async def _run_smoke(sites: list[dict], selected: str) -> None:
    log = logging.getLogger("smoke_test")
    results: dict[str, bool] = {}

    for site in sites:
        name = site["name"]
        if selected != "all" and name != selected:
            continue

        voter_class = _VOTER_CLASSES.get(name)
        if voter_class is None:
            log.warning("Site inconnu ignoré : %s", name)
            continue

        pseudo = sites[0].get("pseudo") or os.environ.get("MINECRAFT_PSEUDO", "")
        voter = voter_class(pseudo=pseudo, url=site["url"])
        log.info("=== Test du site : %s ===", name)
        try:
            await run_vote(voter, headless=False)
            results[name] = True
        except Exception as exc:  # noqa: BLE001
            log.error("Exception inattendue pour %s : %s", name, exc)
            results[name] = False

    # ── Résumé ───────────────────────────────────────────────────────────────
    print("\n" + "=" * 40)
    print("RÉSUMÉ DU SMOKE TEST")
    print("=" * 40)
    for site_name, ok in results.items():
        status = "OK" if ok else "ECHEC"
        print(f"  {site_name:<20} {status}")
    print("=" * 40)


def main() -> None:
    load_dotenv(_PROJECT_ROOT / ".env")
    _configure_logging()
    args = _parse_args()
    config = _load_config()

    # Inject pseudo into each site dict for convenience.
    for site in config.get("sites", []):
        site["pseudo"] = config.get("pseudo", "")

    asyncio.run(_run_smoke(config.get("sites", []), args.site))


if __name__ == "__main__":
    main()
