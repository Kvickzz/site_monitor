# Быстрый Старт

## С Docker Compose (рекомендуется)

### 1. Клонируйте проект
```bash
git clone <repo>
cd site_monitor
```

### 2. Запустите контейнеры
```bash
docker-compose up -d
```

### 3. Примените миграции
```bash
docker-compose exec web python manage.py migrate
```

### 4. Создайте суперпользователя
```bash
docker-compose exec web python manage.py createsuperuser
```

### 5. Откройте в браузере
- Главная страница: http://localhost:8000
- Админ-панель: http://localhost:8000/admin

---

## Локально без Docker

### 1. Установите зависимости

**Linux/Mac:**
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Настройте .env
```bash
cp .env.example .env
# Отредактируйте .env
```

### 3. Запустите миграции
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Запустите сервер (3 терминала)

**Терминал 1:**
```bash
python manage.py runserver
```

**Терминал 2:**
```bash
celery -A config worker -l info
```

**Терминал 3:**
```bash
celery -A config beat -l info
```

### 5. Откройте в браузере
- http://localhost:8000

---

## Первые шаги

### 1. Вход в систему
- Перейдите на http://localhost:8000
- Логин/пароль - те что вы создали при `createsuperuser`

### 2. Добавьте сайт
- Нажмите "+ Добавить сайт"
- Заполните форму:
  - Название: My Website
  - URL: https://example.com
  - Интервал: 300 (5 минут)
  - Таймаут: 10 (секунд)

### 3. Просмотрите результаты
- Дашборд покажет статус сайта
- История проверок в деталях сайта

---

## Полезные команды

```bash
# Создать суперпользователя
python manage.py createsuperuser

# Запустить тесты
python manage.py test

# Очистить старые проверки (> 30 дней)
python manage.py shell
>>> from monitor.tasks import cleanup_old_health_checks
>>> cleanup_old_health_checks.delay()

# Пересчитать статистику
python manage.py shell
>>> from monitor.tasks import calculate_uptime_statistics
>>> calculate_uptime_statistics.delay()

# Вывести логи Docker
docker-compose logs -f web

# Остановить все контейнеры
docker-compose down
```

---

## Проблемы?

### Redis не подключается
```bash
# Проверьте Redis работает
redis-cli ping
# Должен ответить: PONG
```

### БД не применяется
```bash
# Сбросьте миграции
python manage.py migrate monitor zero
python manage.py migrate
```

### Celery не запускается
```bash
# Очистите очередь
celery -A config purge
# Перезапустите worker
celery -A config worker -l info
```

---

Готово! Система мониторинга работает и готова отслеживать доступность ваших сайтов.
