# Déploiement ChezWizi — Render + PostgreSQL + Cloudinary

## Architecture

```
Flutter App  ──HTTPS──►  Render Web Service (Django API)
                              │
                              ├── PostgreSQL (Render, même compte)
                              └── Cloudinary (images produits)
```

---

## 1. Prérequis Git

1. Pousser le projet sur GitHub / GitLab
2. Le dossier API est `restaurant_backend/`

---

## 2. Cloudinary (vous avez déjà les identifiants)

Dans le dashboard Cloudinary, notez :

- **Cloud name**
- **API Key**
- **API Secret**

Vous les ajouterez sur Render à l’étape 4.

---

## 3. Render — PostgreSQL + API (Blueprint)

### Option A — Blueprint (recommandé)

1. [render.com](https://render.com) → **New** → **Blueprint**
2. Connectez le repo, **Root Directory** : `restaurant_backend`
3. Render lit `render.yaml` et crée :
   - une base **PostgreSQL** `chezwizi-db`
   - un **Web Service** `chezwizi-api`
4. `DATABASE_URL` est **liée automatiquement** à l’API (ne pas la saisir à la main)

### Option B — Manuel

1. **New PostgreSQL** → nom `chezwizi`, plan Free → créer
2. **New Web Service** → repo, **Root Directory** `restaurant_backend`
3. **Build** : `./build.sh`
4. **Start** :
   ```
   gunicorn restaurant_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
   ```
5. Dans le Web Service → **Environment** → **Add from database** → choisir la Postgres → variable `DATABASE_URL`

---

## 4. Variables d’environnement (dashboard Render)

Ouvrez le Web Service `chezwizi-api` → **Environment** :

| Variable | Valeur |
|----------|--------|
| `DJANGO_DEBUG` | `false` |
| `SECRET_KEY` | (générée par Render si Blueprint, sinon une clé longue) |
| `DATABASE_URL` | **Déjà fournie** si base liée — ne pas modifier |
| `ALLOWED_HOSTS` | `chezwizi-api-xxxx.onrender.com` (votre hostname exact) |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:8080` (+ URL Flutter web si vous en avez une) |
| `CLOUDINARY_CLOUD_NAME` | votre cloud name |
| `CLOUDINARY_API_KEY` | votre API key |
| `CLOUDINARY_API_SECRET` | votre API secret |

**Exemple** (adapter le hostname) :

```text
ALLOWED_HOSTS=chezwizi-api-xxxx.onrender.com
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://127.0.0.1:8080
CLOUDINARY_CLOUD_NAME=dxxxx
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=xxxxxxxxxxxxxxxxxxxx
```

Enregistrez → Render redéploie. Le build exécute `migrate` via `build.sh`.

---

## 5. Après le premier déploiement réussi

1. Vérifier les **Logs** : `migrate` OK, pas d’erreur `psycopg` / `DATABASE_URL`
2. Créer l’administrateur :
   - Web Service → **Shell**
   ```bash
   python manage.py createsuperuser
   ```
3. Tester l’API : `https://VOTRE-HOST.onrender.com/api/`
4. Admin : `https://VOTRE-HOST.onrender.com/admin/`

**Ne pas** lancer `python seed.py` en production (efface les données).

---

## 6. App Flutter

Remplacez par votre URL Render (sans `/api`) :

```bash
cd restaurant_app
flutter pub get

flutter build apk --release --dart-define=API_BASE_URL=https://chezwizi-api-xxxx.onrender.com
```

Test téléphone sur le même réseau que le PC (dev) :

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.x.x:8000
```

---

## 7. Vérifications

| Test | OK si… |
|------|--------|
| Login app | Pas d’erreur CORS / 400 |
| Créer un produit + photo | `image_url` commence par `https://res.cloudinary.com/` |
| Admin Django | Connexion superuser |

---

## 8. Développement local

Sans `DATABASE_URL` → **SQLite** + dossier `media/`.

Pour coller à la prod : copiez `.env.example` → `.env`, ajoutez Cloudinary et éventuellement `DATABASE_URL` (Internal Database URL depuis Render, usage dev uniquement).

```bash
cd restaurant_backend
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

## Dépannage

| Problème | Piste |
|----------|--------|
| `could not connect to server` | `DATABASE_URL` absente ou base pas liée au Web Service |
| `SSL connection required` | Normal en prod ; `settings.py` force SSL si `DJANGO_DEBUG=false` |
| Images invisibles | Vérifier les 3 variables `CLOUDINARY_*` |
| CORS / login depuis le web | Ajouter l’URL exacte du navigateur dans `CORS_ALLOWED_ORIGINS` |
| Service qui dort (plan free) | Premier appel lent (~30 s) — normal sur Render Free |
