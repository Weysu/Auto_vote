# Auto Vote — Minecraft

Bot de vote automatique pour les serveurs Minecraft. Gère trois sites de listing simultanément, résout les captchas via 2Captcha, et respecte une fenêtre horaire configurable avec un comportement humain simulé.

---

## Sites supportés

| Site | Captcha | Intervalle |
|------|---------|------------|
| liste-serveurs-minecraft.org | reCAPTCHA invisible | 3h |
| serveur-prive.net | MTCaptcha | 1h30 |
| serveur-minecraft.com | reCAPTCHA v2 | 3h |

---

## Prérequis

- Python 3.12+
- Un compte [2Captcha](https://2captcha.com) avec du crédit
- Docker (pour le déploiement VPS)

---

## Installation

```bash
git clone https://github.com/Weysu/Auto_vote.git
cd Auto_vote

pip install -r requirements.txt
playwright install chromium
```

---

## Configuration

### 1. Clé API 2Captcha

Crée un compte sur [2captcha.com](https://2captcha.com), recharge du crédit (minimum recommandé : 5$), puis récupère ta clé API dans le dashboard.

Le coût moyen est de ~0.003$ par captcha résolu.

### 2. Fichier `.env`

Copie le fichier d'exemple et remplis les valeurs :

```bash
cp .env.example .env
```

```env
MINECRAFT_PSEUDO=TonPseudo
TWOCAPTCHA_API_KEY=ta_clé_api_ici
```

### 3. `config.yaml`

Les intervalles et URLs sont préconfigurés. Tu peux ajuster les valeurs si nécessaire :

```yaml
pseudo: ${MINECRAFT_PSEUDO}
sites:
  - name: lsm
    url: https://www.liste-serveurs-minecraft.org/vote/?idc=202832
    interval_hours: 3
    jitter_seconds: 900
  - name: serveur_prive
    url: https://serveur-prive.net/minecraft/neodium-2142/vote
    interval_hours: 1.5
    jitter_seconds: 900
  - name: serveur_mc
    url: https://serveur-minecraft.com/2642
    interval_hours: 3
    jitter_seconds: 900
```

`jitter_seconds` définit le décalage aléatoire maximum appliqué à chaque vote (en secondes). Cela simule un comportement humain en évitant des votes à la seconde près.

---

## Lancement

### En local

```bash
cd minecraft-voter
python src/main.py
```

### Avec Docker

```bash
docker build -t auto-vote .
docker run -d \
  --name auto-vote \
  --env-file .env \
  --restart unless-stopped \
  auto-vote
```

---

## Tests

Un script de smoke test permet de valider chaque voter indépendamment avant de lancer le scheduler complet.

```bash
# Tester un site spécifique
python tests/smoke_test.py --site lsm
python tests/smoke_test.py --site serveur_prive
python tests/smoke_test.py --site serveur_mc

# Tester les trois en séquence
python tests/smoke_test.py --site all
```

Le navigateur s'ouvre en mode visible (`headless=False`) pour permettre l'inspection manuelle.

---

## Structure du projet

```
minecraft-voter/
├── src/
│   ├── voters/
│   │   ├── base.py           # Classe abstraite BaseVoter
│   │   ├── captcha.py        # Résolution captcha via 2Captcha
│   │   ├── lsm.py            # liste-serveurs-minecraft.org
│   │   ├── serveur_prive.py  # serveur-prive.net
│   │   └── serveur_mc.py     # serveur-minecraft.com
│   ├── scheduler.py          # APScheduler — jobs one-shot avec jitter
│   └── main.py               # Point d'entrée
├── tests/
│   └── smoke_test.py         # Tests manuels par site
├── config.yaml               # Intervalles et URLs par site
├── Dockerfile
├── requirements.txt
└── .env.example
```

---

## Comportement du scheduler

Les votes tournent en parallèle, chacun sur son propre cycle indépendant. Après chaque vote, le prochain est planifié avec un décalage aléatoire entre 0 et 15 minutes.

Les votes sont limités à la plage **7h30 — 00h30 (heure de Paris)**. Si le prochain vote calculé tombe en dehors de cette fenêtre, il est automatiquement décalé à 7h30.

---

## Dépannage

**`ERROR_WRONG_USER_KEY`** — La clé 2Captcha dans `.env` est incorrecte ou vide. Vérifie qu'il n'y a pas d'espace autour de la valeur.

**Bouton introuvable / Timeout** — Le site a probablement un cooldown actif (vote déjà effectué récemment). Le scheduler réessaiera automatiquement au prochain cycle.

**Modale RGPD bloquante** — Le consentement n'est pas persisté entre sessions Playwright. Le code gère automatiquement les modales connues au démarrage de chaque vote.

---

## Déploiement VPS

Le `.env` ne doit jamais être copié dans l'image Docker. Il est monté au runtime :

```bash
docker run -d \
  --name auto-vote \
  --env-file /chemin/vers/.env \
  --restart unless-stopped \
  auto-vote
```

Pour mettre à jour après un push :

```bash
git pull
docker build -t auto-vote .
docker stop auto-vote && docker rm auto-vote
docker run -d --name auto-vote --env-file .env --restart unless-stopped auto-vote
```
