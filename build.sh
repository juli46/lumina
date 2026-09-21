#!/usr/bin/env bash
set -o errexit

echo "=== INSTALANDO DEPENDENCIAS ==="
pip install -r requirements.txt

echo "=== COMPROBANDO MEDIA (solo informativo, no rompe el build) ==="
pwd
ls -lh media/productos/queen.webp || echo "AVISO: media/productos/queen.webp no existe en el repo"
ls -lh media/productos 2>/dev/null | head -20 || echo "AVISO: carpeta media/productos no existe"

echo "=== COLLECTSTATIC ==="
python manage.py collectstatic --noinput

echo "=== MIGRACIONES ==="
python manage.py migrate --noinput

echo "=== CONFIGURANDO GOOGLE ALLAUTH ==="
python manage.py shell <<'EOF'
import os
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site

client_id = os.getenv("GOOGLE_CLIENT_ID")
client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

if not client_id or not client_secret:
    print("AVISO: GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET no definidos, se omite Google Allauth")
else:
    domain = os.getenv("RENDER_EXTERNAL_HOSTNAME", "localhost")
    site, _ = Site.objects.update_or_create(
        id=1, defaults={"domain": domain, "name": domain}
    )

    app, _ = SocialApp.objects.get_or_create(
        provider="google", defaults={"name": "Google"}
    )
    app.client_id = client_id
    app.secret = client_secret
    app.save()
    app.sites.add(site)
    print("Google SocialApp OK:", app.client_id, "| Site:", site.domain)
EOF
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); import config.wsgi; print('WSGI OK')"
echo "=== BUILD TERMINADO ==="