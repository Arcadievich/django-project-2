#!/bin/bash
set -e


PROJECT_DIR="/opt/django-project-2"
BRANCH="master"
VENV_DIR="$PROJECT_DIR/venv"
SERVICE_NAME="django-project"


echo "Деплой запускается..."

cd $PROJECT_DIR
git pull origin $BRANCH
npm ci --dev
source $VENV_DIR/bin/activate
pip install -r requirements.txt
python3 manage.py collectstatic --noinput
python3 manage.py migrate
sudo systemctl restart nginx
sudo systemctl restart $SERVICE_NAME

echo "Деплой завершен успешно"
