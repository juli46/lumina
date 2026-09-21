#!/usr/bin/env bash

set -o errexit

echo "=== COMPROBANDO MEDIA ==="

pwd

echo "--- archivo queen ---"

ls -lh media/productos/queen.webp

echo "--- carpeta media/productos ---"

ls -lh media/productos | head -20

echo "=== FIN COMPROBACION MEDIA ==="

pip install -r requirements.txt

echo "=== DJANGO MEDIA CONFIG ==="

python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); import django; django.setup(); from django.conf import settings; print('MEDIA_ROOT =', settings.MEDIA_ROOT); print('EXISTS =', os.path.exists(settings.MEDIA_ROOT)); print('FILE EXISTS =', os.path.exists(os.path.join(settings.MEDIA_ROOT, 'productos', 'queen.webp')))"

echo "=== FIN DJANGO MEDIA CONFIG ==="

python manage.py migrate

echo "=== CONFIGURANDO GOOGLE ALLAUTH ==="

python manage.py shell -c "import os; from allauth.socialaccount.models import SocialApp; from django.contrib.sites.models import Site; client_id=os.getenv('GOOGLE_CLIENT_ID'); client_secret=os.getenv('GOOGLE_CLIENT_SECRET'); app=SocialApp.objects.filter(provider='google').first(); app.client_id=client_id; app.secret=client_secret; app.save(); app.sites.add(Site.objects.get(id=1)); print('Google SocialApp actualizado correctamente:', app.client_id)"

echo "=== FIN CONFIGURACION GOOGLE ALLAUTH ==="

python manage.py collectstatic --noinput