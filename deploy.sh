#!/bin/bash
set -e


PROJECT_DIR="/opt/django-project-2"
BRANCH="master"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="django-project"


echo "Деплой запускается..."

cd $PROJECT_DIR || echo "Ошибка при переходе в директорию проекта"

git pull origin $BRANCH || echo "Ошибка при загрузки обновлений с github"

npm ci --dev || echo "Ошибка при обновлении библиотек Node.js"

source $VENV_DIR/bin/activate || echo "Ошибка при запуске виртуальной среды"

pip install -r requirements.txt || echo "Ошибка при обновлении библиотек Python"

python3 manage.py collectstatic --noinput || echo "Ошибка при обновлении файлов статики"

python3 manage.py migrate || echo "Ошибка при запуске миграций БД"

sudo systemctl restart nginx || echo "Ошибка при перезапуске nginx"

sudo systemctl restart $SERVICE_NAME || echo "Ошибка при перезапуске сайта"

echo "Деплой завершен успешно"
