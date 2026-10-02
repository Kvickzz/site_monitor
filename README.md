# Site Monitor

Django приложение для мониторинга доступности веб-сайтов.

## Особенности

- Мониторинг доступности сайтов в реальном времени
- Сохранение истории проверок
- Расчет статистики uptime
- Система уведомлений (Email, Telegram, Slack, Webhook)
- REST API для интеграции
- Celery для фоновых задач
- PostgreSQL для надежного хранения данных

## Требования

- Python 3.11+
- PostgreSQL 13+
- Redis 7+
- Docker & Docker Compose (опционально)

## Быстрый старт

### 1. Клонирование и установка

```bash
# Клонировать репозиторий
git clone <repo>
cd site_monitor

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка

```bash
# Скопировать файл конфигурации
cp .env.example .env

# Отредактировать .env с вашими параметрами
nano .env
```

### 3. Инициализация БД

```bash
# Применить миграции
python manage.py migrate

# Создать суперпользователя
python manage.py createsuperuser
```

### 4. Запуск

```bash
# Запустить Django сервер
python manage.py runserver

# В отдельном окне запустить Celery worker
celery -A config worker -l info

# В еще одном окне запустить Celery beat (scheduler)
celery -A config beat -l info
```

## Запуск с Docker

```bash
# Собрать и запустить контейнеры
docker-compose up -d

# Применить миграции
docker-compose exec web python manage.py migrate

# Создать суперпользователя
docker-compose exec web python manage.py createsuperuser
```

Приложение будет доступно по адресу: **http://localhost:8000**

Админ-панель: **http://localhost:8000/admin**

## Использование

### Добавление сайта

1. Перейдите в раздел "Добавить сайт"
2. Заполните форму:
   - Название сайта
   - URL (например: https://example.com)
   - Интервал проверки (в секундах)
   - Таймаут (в секундах)
3. Нажмите "Добавить сайт"

### Просмотр статистики

- **Дашборд** - общий обзор всех сайтов
- **Список сайтов** - детальный список с фильтрацией
- **Детали сайта** - история проверок и статистика
- **Статистика** - общие метрики и аналитика

### Настройка уведомлений

В админ-панели создайте каналы уведомлений:
- Email
- Telegram
- Slack
- Webhook

## API

REST API доступен по адресу `/api/`

### Примеры

```bash
# Получить список сайтов
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/websites/

# Проверить сайт сейчас
curl -X POST -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/websites/<id>/check_now/

# Получить историю проверок
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/health-checks/?website_id=<id>
```

## Структура проекта

```
site_monitor/
├── config/           # Конфигурация Django
├── monitor/          # Основное приложение
├── templates/        # HTML шаблоны
├── static/          # Статические файлы
├── tests/           # Тесты
├── requirements.txt # Зависимости
└── manage.py        # Django CLI
```

## Переменные окружения

- `DEBUG` - Режим отладки (True/False)
- `SECRET_KEY` - Секретный ключ Django
- `DB_NAME` - Имя БД PostgreSQL
- `DB_USER` - Пользователь БД
- `DB_PASSWORD` - Пароль БД
- `DB_HOST` - Хост БД
- `DB_PORT` - Порт БД
- `REDIS_URL` - URL Redis
- `ALLOWED_HOSTS` - Разрешенные хосты

## Тестирование

```bash
# Запустить тесты
python manage.py test

# С покрытием
pytest --cov=monitor
```

## Разработка

### Миграции БД

```bash
# Создать миграцию
python manage.py makemigrations

# Применить миграции
python manage.py migrate

# Откатить миграцию
python manage.py migrate monitor 0001
```

### Celery задачи

Основные задачи:
- `check_website_health` - проверка доступности сайта
- `check_all_websites` - проверка всех активных сайтов
- `calculate_uptime_statistics` - расчет статистики
- `cleanup_old_health_checks` - удаление старых записей

## Troubleshooting

### Celery не запускается
```bash
# Проверить Redis
redis-cli ping

# Переучить Celery
celery -A config purge
```

### Миграции не работают
```bash
# Удалить старые миграции и пересоздать
python manage.py migrate monitor zero
python manage.py migrate
```

## Лицензия

MIT

## Поддержка

Для вопросов и проблем создавайте Issues в репозитории.
