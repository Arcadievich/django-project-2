FROM python:3.11.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt
RUN pip install psycopg2-binary==2.9.12

COPY foodcartapp ./foodcartapp
COPY placesapp ./placesapp
COPY restaurateur ./restaurateur
COPY star_burger ./star_burger
COPY templates ./templates
COPY manage.py .
COPY .env .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]