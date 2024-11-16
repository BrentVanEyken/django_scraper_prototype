# django_scraper_prototype

## Please run the following commands in cmd:

python -m venv venv

venv\scripts\activate

python manage.py runserver

pip install -r requirements.txt

playwright install

redis-server

## after install docker desktop run the following command in cmd:

### If the container isn't created yet:
docker run -d -p 6379:6379 --name celery_redis redis:latest
### If the container has already been created:
docker start celery_redis

## TO run a celery worker run the following commands in cmd:

cd ./myproject

celery -A myproject worker --loglevel=info --autoscale=20,3

