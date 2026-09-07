#!/bin/bash
set -e

PROJECT_DIR="/opt/django-project-2"
BRANCH="master"
SERVICE_NAME="django-project"

echo "Деплой запускается..."

cd $PROJECT_DIR
docker-compose down
git pull origin $BRANCH
docker-compose --profile builder up --build frontend-builder
docker-compose --profile builder up --build django-migrate-collectstatic
docker-compose up -d --build web
sudo systemctl restart nginx
sudo systemctl restart $SERVICE_NAME

echo "Деплой завершен успешно"

set -a
source .env
set +a

curl -s -H "X-Rollbar-Access-Token: $ROLLBAR_ACCESS_TOKEN" \
     -H "Content-Type: application/json" \
     -X POST "https://api.rollbar.com/api/1/deploy" \
     -d '{
          "environment": "'"$ROLLBAR_ENVIRONMENT"'",
          "revision": "'"$(git rev-parse HEAD)"'",
          "local_username": "'"$(whoami)"'",
          "comment": "Deploy via script from '"$(hostname)"'",
          "status": "succeeded"
         }'

echo "Уведомление в Rollbar отправлено"