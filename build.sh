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

python manage.py migrate

python manage.py collectstatic --noinput