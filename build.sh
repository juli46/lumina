#!/usr/bin/env bash
set -o errexit

echo "=== COMPROBANDO MEDIA ==="
pwd
echo "--- archivo queen ---"
ls -lh media/productos/queen.webp
echo "--- carpeta media/productos ---"
ls -lh media/productos | head -20
echo "=== FIN COMPROBACION MEDIA ==="
echo "=== DJANGO MEDIA CONFIG ==="
python -c "import os; os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings'); import django; django.setup(); from django.conf import settings; import os.path; print('MEDIA_ROOT =', settings.MEDIA_ROOT); print('EXISTS =', os.path.exists(settings.MEDIA_ROOT)); print('FILE EXISTS =', os.path.exists(os.path.join(settings.MEDIA_ROOT, 'productos', 'queen.webp')))"
echo "=== FIN DJANGO MEDIA CONFIG ==="

python manage.py migrate

python manage.py collectstatic --noinput