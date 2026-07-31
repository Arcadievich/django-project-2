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
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
source $VENV_DIR/bin/activate
pip install -r requirements.txt
python3 manage.py collectstatic --noinput
python3 manage.py migrate
sudo systemctl restart nginx
sudo systemctl restart $SERVICE_NAME

echo "Деплой завершен успешно"

set -a
source .env
set +a

curl -s -H "X-Rollbar-Access_Token: $ROLLBAR_ACCESS_TOKEN" \
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