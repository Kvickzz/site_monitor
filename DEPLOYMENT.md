# Развертывание в Production

## На VPS/сервере

### 1. Подготовка сервера

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить необходимое ПО
sudo apt install -y python3.11 python3.11-venv postgresql postgresql-contrib nginx redis-server git

# Создать пользователя приложения
sudo useradd -m -d /home/sitemonitor -s /bin/bash sitemonitor
sudo su - sitemonitor
```

### 2. Клонирование проекта

```bash
# В директории /home/sitemonitor/
git clone <repo> app
cd app
```

### 3. Виртуальное окружение и зависимости

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn
```

### 4. Настройка PostgreSQL

```bash
# Как пользователь postgres
sudo -u postgres psql

# В psql:
CREATE DATABASE site_monitor;
CREATE USER sitemonitor WITH PASSWORD 'strong_password_here';
ALTER ROLE sitemonitor SET client_encoding TO 'utf8';
ALTER ROLE sitemonitor SET default_transaction_isolation TO 'read committed';
ALTER ROLE sitemonitor SET default_transaction_deferrable TO on;
ALTER ROLE sitemonitor SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE site_monitor TO sitemonitor;
\q
```

### 5. Конфигурация приложения

```bash
# Создать .env
cat > /home/sitemonitor/app/.env << EOF
DEBUG=False
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgresql://sitemonitor:strong_password@localhost:5432/site_monitor
REDIS_URL=redis://localhost:6379/0
EOF

# Задать права
chmod 600 /home/sitemonitor/app/.env
```

### 6. Инициализация БД

```bash
cd /home/sitemonitor/app
source venv/bin/activate

python manage.py collectstatic --noinput
python manage.py migrate
python manage.py createsuperuser
```

### 7. Systemd сервисы

**Создать /etc/systemd/system/sitemonitor.service:**
```ini
[Unit]
Description=Site Monitor Gunicorn Service
After=network.target
Requires=sitemonitor-celery.service

[Service]
Type=notify
User=sitemonitor
Group=www-data
WorkingDirectory=/home/sitemonitor/app
ExecStart=/home/sitemonitor/app/venv/bin/gunicorn \
    --workers 4 \
    --worker-class gthread \
    --threads 2 \
    --worker-tmp-dir /dev/shm \
    --bind unix:/home/sitemonitor/app/gunicorn.sock \
    config.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Создать /etc/systemd/system/sitemonitor-celery.service:**
```ini
[Unit]
Description=Site Monitor Celery Worker
After=network.target redis-server.service

[Service]
Type=forking
User=sitemonitor
Group=www-data
WorkingDirectory=/home/sitemonitor/app
ExecStart=/home/sitemonitor/app/venv/bin/celery -A config worker \
    --loglevel=info \
    --logfile=/var/log/sitemonitor/celery-worker.log \
    --pidfile=/var/run/sitemonitor/celery-worker.pid

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Создать /etc/systemd/system/sitemonitor-celery-beat.service:**
```ini
[Unit]
Description=Site Monitor Celery Beat
After=network.target redis-server.service

[Service]
Type=simple
User=sitemonitor
Group=www-data
WorkingDirectory=/home/sitemonitor/app
ExecStart=/home/sitemonitor/app/venv/bin/celery -A config beat \
    --loglevel=info \
    --logfile=/var/log/sitemonitor/celery-beat.log

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 8. Создать директории логов

```bash
sudo mkdir -p /var/log/sitemonitor
sudo mkdir -p /var/run/sitemonitor
sudo chown sitemonitor:www-data /var/log/sitemonitor /var/run/sitemonitor
```

### 9. Активировать сервисы

```bash
sudo systemctl daemon-reload
sudo systemctl enable sitemonitor
sudo systemctl enable sitemonitor-celery
sudo systemctl enable sitemonitor-celery-beat
sudo systemctl start sitemonitor
sudo systemctl start sitemonitor-celery
sudo systemctl start sitemonitor-celery-beat

# Проверить статус
sudo systemctl status sitemonitor
sudo systemctl status sitemonitor-celery
sudo systemctl status sitemonitor-celery-beat
```

### 10. Настройка Nginx

**Создать /etc/nginx/sites-available/sitemonitor:**
```nginx
upstream sitemonitor {
    server unix:/home/sitemonitor/app/gunicorn.sock fail_timeout=0;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    client_max_body_size 10M;

    location /static/ {
        alias /home/sitemonitor/app/staticfiles/;
    }

    location /media/ {
        alias /home/sitemonitor/app/media/;
    }

    location / {
        proxy_pass http://sitemonitor;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}

# HTTPS редирект
server {
    listen 80;
    server_name _;
    return 301 https://$host$request_uri;
}
```

### 11. Включить Nginx

```bash
sudo ln -s /etc/nginx/sites-available/sitemonitor /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# Проверить конфиг
sudo nginx -t

# Перезагрузить
sudo systemctl restart nginx
```

### 12. SSL (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y

sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Обновить конфиг Nginx для HTTPS
# (certbot сделает это автоматически)
```

### 13. Мониторинг логов

```bash
# Django логи
tail -f /var/log/sitemonitor/django.log

# Celery логи
tail -f /var/log/sitemonitor/celery-worker.log
tail -f /var/log/sitemonitor/celery-beat.log

# Nginx логи
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## Docker на Heroku

```bash
# Логин в Heroku
heroku login

# Создать приложение
heroku create sitemonitor

# Установить PostgreSQL add-on
heroku addons:create heroku-postgresql:standard-0 -a sitemonitor

# Установить Redis add-on
heroku addons:create heroku-redis:premium-0 -a sitemonitor

# Настроить environment variables
heroku config:set SECRET_KEY="your-secret-key" -a sitemonitor
heroku config:set DEBUG=False -a sitemonitor

# Развернуть
git push heroku main

# Применить миграции
heroku run python manage.py migrate -a sitemonitor

# Создать суперпользователя
heroku run python manage.py createsuperuser -a sitemonitor

# Посмотреть логи
heroku logs -f -a sitemonitor
```

## Backup и Restore

```bash
# Backup БД
sudo -u postgres pg_dump site_monitor > /backups/sitemonitor-db-$(date +%Y%m%d).sql

# Restore БД
sudo -u postgres psql site_monitor < /backups/sitemonitor-db-20240101.sql

# Backup media
tar -czf /backups/sitemonitor-media-$(date +%Y%m%d).tar.gz /home/sitemonitor/app/media/
```

## Мониторинг production

### Установить Sentry (опционально)

```bash
pip install sentry-sdk

# Добавить в settings.py
import sentry_sdk
sentry_sdk.init(dsn="your-sentry-dsn")
```

### Включить CORS если нужен API

```python
# settings.py
CORS_ALLOWED_ORIGINS = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
]
```

## Обновление проекта

```bash
cd /home/sitemonitor/app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart sitemonitor
```
