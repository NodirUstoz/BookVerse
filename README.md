<div align="center">

# 📚 BookVerse

**Современная книжная вселенная: онлайн-магазин, читательская платформа и социальная сеть для книголюбов — всё в одном продукте.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14-A30000?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![Elasticsearch](https://img.shields.io/badge/Elasticsearch-8.x-005571?logo=elasticsearch&logoColor=white)](https://www.elastic.co/)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](https://docs.docker.com/compose/)
[![Nginx](https://img.shields.io/badge/Nginx-Reverse_Proxy-009639?logo=nginx&logoColor=white)](https://nginx.org/)
[![Stripe](https://img.shields.io/badge/Stripe-Payments-635BFF?logo=stripe&logoColor=white)](https://stripe.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](#-лицензия)

</div>

---

## 📑 Содержание

1. [О проекте](#-1-о-проекте)
2. [Ключевые возможности](#-2-ключевые-возможности)
3. [Технологический стек](#-3-технологический-стек)
4. [Структура репозитория](#-4-структура-репозитория)
5. [Архитектура и как это работает](#-5-архитектура-и-как-это-работает)
6. [Доменная модель (крупными блоками)](#-6-доменная-модель-крупными-блоками)
7. [Сервисы в Docker Compose](#-7-сервисы-в-docker-compose)
8. [Быстрый старт (локально, Docker)](#-8-быстрый-старт-локально-docker)
9. [Основные команды Makefile](#-9-основные-команды-makefile)
10. [Ручной запуск frontend и backend](#-10-ручной-запуск-frontend-и-backend)
11. [Конфигурация и переменные окружения](#-11-конфигурация-и-переменные-окружения)
12. [API, очереди и интеграции](#-12-api-очереди-и-интеграции)
13. [Мониторинг и эксплуатация](#-13-мониторинг-и-эксплуатация)
14. [CI/CD](#-14-cicd)
15. [Безопасность и работа с данными](#-15-безопасность-и-работа-с-данными)
16. [Роли компонентов в продакшене](#-16-роли-компонентов-в-продакшене)
17. [Лицензия](#-17-лицензия)
18. [Поддержка](#-18-поддержка)

---

## 🚀 1. О проекте

**BookVerse** — это **продуктовая SaaS-платформа** для чтения и покупки книг: каталог, рекомендации, прогресс чтения, книжные клубы, отзывы, списки желаемого и полноценный e-commerce checkout — всё в одном окне. Система рассчитана на конечных читателей (веб-интерфейс), команды модераторов и контент-кураторов (admin), а также интеграторов (REST API), с возможностью эксплуатации в Docker — от локальной разработки до production.

### Что это за тип системы

По архитектуре BookVerse — **многосервисная распределённая платформа** (не монолит «в одном процессе»):

| Аспект          | Описание                                                                                       |
|-----------------|------------------------------------------------------------------------------------------------|
| **Продукт**     | B2C-сервис чтения и продажи книг с социальными функциями, рекомендациями и e-commerce          |
| **Архитектура** | Микросервисная: Django REST API, React SPA, Celery workers, Elasticsearch, Nginx-прокси        |
| **Хранилище**   | PostgreSQL (метаданные и транзакции) + Elasticsearch (полнотекстовый поиск) + Redis (кэш/брокер) |
| **Платежи**     | Stripe (заказы, подписки, возвраты)                                                            |
| **Авторизация** | JWT (SimpleJWT) + django-allauth (social-login)                                                |
| **Эксплуатация**| Docker Compose: dev = одним `make up`, prod = compose-overlay с TLS, gunicorn, beat-планировщик |

### Для кого

- 📖 **Читатели** — собирают библиотеку, ведут прогресс чтения, получают рекомендации, вступают в книжные клубы.
- 🛒 **Покупатели** — заказывают бумажные/электронные книги, оплачивают через Stripe, отслеживают доставку.
- ✍️ **Авторы и издатели** — управляют страницами авторов, библиографиями, промо-материалами.
- 🛡️ **Администраторы** — модерируют контент, ведут инвентарь, смотрят аналитику продаж.
- 🔌 **Интеграторы** — встраивают BookVerse через REST API (OpenAPI-spec, JWT).

---

## ✨ 2. Ключевые возможности

### 🛒 Книжный магазин
- Каталог книг с расширенной фильтрацией (жанры, авторы, цена, рейтинг, год, язык)
- Детальные страницы книг: описание, автор, издатель, превью, отзывы
- Жанровая навигация, кураторские подборки, бестселлеры, выбор редакции
- Корзина, безопасный checkout через **Stripe**, отслеживание заказов
- Многоуровневые скидки, промокоды, подарочные сертификаты

### 📚 Платформа для чтения
- Личные списки: **Хочу прочитать**, **Читаю сейчас**, **Прочитано**
- Отслеживание прогресса с точностью до страницы и времени чтения
- **Книжные клубы**: совместное чтение, обсуждения, общие цели
- Персонализированные рекомендации на основе **collaborative filtering**
- Список желаемого с возможностью поделиться публичной ссылкой

### 💬 Социальное и отзывы
- Звёздные рейтинги и развёрнутые письменные обзоры
- Голосование «Полезный отзыв» — комьюнити-фильтрация качества
- Страницы авторов с биографиями и полной библиографией
- Профили пользователей со статистикой чтения и историей активности

### 🛡️ Администрирование
- Полноценный admin-дашборд: инвентарь, заказы, пользователи
- Аналитика продаж и отчётность
- Инструменты модерации и управления контентом
- Кураторские полки: featured, bestsellers, staff picks
- Health-check и встроенные метрики

### 🔍 Поиск и индексирование
- Полнотекстовый поиск через **Elasticsearch**
- Автодополнение, опечатки (fuzzy matching), синонимы
- Фасетные фильтры по жанрам, авторам, тегам

---

## 🧰 3. Технологический стек

| Слой              | Технология                                                                            |
|-------------------|---------------------------------------------------------------------------------------|
| **Backend**       | Python 3.11+, Django 4.2, Django REST Framework 3.14, drf-spectacular (OpenAPI)        |
| **Frontend**      | React 18, Redux Toolkit, React Router, Axios                                          |
| **База данных**   | PostgreSQL 15 (alpine)                                                                |
| **Кэш / брокер**  | Redis 7 (cache + Celery broker + result backend)                                      |
| **Очередь задач** | Celery 5.3 + django-celery-beat (cron-задачи в БД)                                    |
| **Поиск**         | Elasticsearch 8.x + django-elasticsearch-dsl-drf                                       |
| **Аутентификация**| djangorestframework-simplejwt, django-allauth, dj-rest-auth                            |
| **Платежи**       | Stripe Python SDK                                                                     |
| **Хранилище медиа** | django-storages + boto3 (S3-совместимое)                                            |
| **Reverse Proxy** | Nginx 1.25                                                                            |
| **Production WSGI** | Gunicorn + WhiteNoise                                                               |
| **Контейнеризация** | Docker, Docker Compose v2                                                           |
| **Тесты**         | pytest, pytest-django, factory-boy, faker, coverage                                   |
| **Качество кода** | black, isort, flake8, mypy, eslint, prettier                                          |
| **Мониторинг**    | Sentry SDK, django-health-check, Celery Flower                                        |

---

## 📂 4. Структура репозитория

```text
BookVerse/
├── backend/                       # Django REST API
│   ├── apps/                      # Бизнес-приложения (bounded contexts)
│   │   ├── accounts/              # Пользователи, профили, аутентификация
│   │   ├── books/                 # Книги, авторы, жанры, издатели
│   │   ├── catalog/               # Витрины: featured, bestsellers, collections
│   │   ├── orders/                # Корзина, заказы, Stripe-платежи
│   │   ├── reviews/               # Рейтинги, отзывы, голосование
│   │   ├── reading/               # Списки чтения, прогресс, книжные клубы
│   │   ├── recommendations/       # Движок рекомендаций (collaborative filtering)
│   │   └── wishlist/              # Списки желаемого, шаринг
│   ├── config/                    # Корневая конфигурация Django
│   │   ├── settings/              # base / development / production
│   │   ├── urls.py                # Корневой роутер
│   │   ├── wsgi.py · asgi.py      # WSGI/ASGI entrypoints
│   │   └── celery.py              # Celery app + autodiscover
│   ├── utils/                     # Общие утилиты (пагинация, permissions, helpers)
│   ├── manage.py                  # Django CLI
│   └── requirements.txt           # Pinned зависимости
│
├── frontend/                      # React SPA
│   ├── public/                    # Статика, index.html, favicon
│   └── src/
│       ├── api/                   # Axios-клиенты, service-модули
│       ├── components/            # Переиспользуемые UI-компоненты
│       ├── pages/                 # Страницы (route-level)
│       ├── store/                 # Redux Toolkit slices + RTK Query
│       ├── hooks/                 # Кастомные React-хуки
│       └── styles/                # Глобальные стили, темы
│
├── nginx/
│   └── nginx.conf                 # Reverse proxy, статика, gzip, SSL
│
├── docker-compose.yml             # 7 сервисов: db, redis, es, backend, celery_worker, celery_beat, frontend, nginx
├── Makefile                       # Удобные команды для dev/ops
├── .env.example                   # Шаблон переменных окружения
└── README.md
```

---

## 🏗️ 5. Архитектура и как это работает

BookVerse построен по принципу **разделения ответственности на независимые сервисы**, каждый из которых живёт в собственном контейнере и общается с другими по чётко определённым контрактам.

```
                                    ┌─────────────────────┐
                                    │   Пользователь /    │
                                    │    Браузер / SPA    │
                                    └──────────┬──────────┘
                                               │ HTTPS
                                               ▼
                                    ┌─────────────────────┐
                                    │   Nginx (80/443)    │
                                    │  Reverse Proxy +    │
                                    │  Static / Media     │
                                    └──────┬──────────┬───┘
                                           │          │
                          ┌────────────────┘          └────────────────┐
                          ▼                                            ▼
              ┌────────────────────┐                       ┌─────────────────────┐
              │  React SPA :3000   │                       │  Django REST API    │
              │  Redux + RTK Query │ ───── REST/JSON ───▶  │  Gunicorn :8000     │
              └────────────────────┘                       └──┬───────────┬──────┘
                                                              │           │
                              ┌───────────────────────────────┘           │
                              │                                           │
                              ▼                                           ▼
                  ┌─────────────────────┐                  ┌──────────────────────────┐
                  │   PostgreSQL :5432  │                  │      Redis :6379         │
                  │  Транзакционные     │                  │   Cache + Celery Broker  │
                  │  данные, заказы,    │                  │   + Result Backend       │
                  │  пользователи       │                  └────────┬─────────────────┘
                  └─────────────────────┘                           │
                              ▲                                     │
                              │                            ┌────────┴─────────┐
                              │                            ▼                  ▼
                              │                  ┌──────────────────┐  ┌────────────────┐
                              │                  │  Celery Worker   │  │  Celery Beat   │
                              │                  │ (фоновые задачи) │  │  (cron-планир.)│
                              │                  └────────┬─────────┘  └────────────────┘
                              │                           │
                              └───────────────────────────┘
                                                                 │
                                                                 ▼
                                                      ┌─────────────────────┐
                                                      │ Elasticsearch :9200 │
                                                      │   Full-text search  │
                                                      └─────────────────────┘
```

### Как идёт запрос (на примере «открыл страницу книги»)

1. Пользователь делает HTTPS-запрос → **Nginx** терминирует TLS и маршрутизирует трафик.
2. Статические маршруты (`/static/`, `/media/`) Nginx отдаёт напрямую с тома.
3. Запросы `/api/*` уходят на **Django + Gunicorn**, остальное (`/`) — на React SPA.
4. Django читает метаданные книги из **PostgreSQL**, агрегаты по рейтингам — из **Redis-кэша**.
5. Связанные товары и рекомендации подтягиваются из **Elasticsearch** и предрасчитанных таблиц.
6. Тяжёлые операции (отправка писем, пересчёт рекомендаций, реиндексация ES) откладываются в очередь Redis → их подхватывает **Celery Worker**.
7. Регулярные задачи (ежедневная пересборка топа продаж, очистка корзин) запускает **Celery Beat**.

---

## 🧱 6. Доменная модель (крупными блоками)

| Контекст              | Ключевые сущности                                                       | Описание                                                                                          |
|-----------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------|
| **Accounts**          | `User`, `Profile`, `Address`                                            | Аутентификация (JWT + social), профили читателей, адреса доставки                                 |
| **Books**             | `Book`, `Author`, `Genre`, `Publisher`, `Tag`                           | Каталог произведений, авторов, жанров — ядро системы                                              |
| **Catalog**           | `FeaturedShelf`, `Bestseller`, `Collection`, `StaffPick`                | Витрины и кураторские полки на главной                                                            |
| **Orders**            | `Cart`, `CartItem`, `Order`, `OrderItem`, `Payment`, `Shipment`         | Корзина, оформление заказа, Stripe-платежи, доставка                                              |
| **Reviews**           | `Review`, `Rating`, `HelpfulVote`                                       | Звёздные рейтинги, текстовые отзывы, голосование за полезность                                    |
| **Reading**           | `ReadingList`, `ReadingProgress`, `BookClub`, `ClubMembership`, `ClubPost` | Полки чтения, прогресс по страницам, книжные клубы и обсуждения                                |
| **Recommendations**   | `UserPreference`, `Similarity`, `RecommendationCache`                   | Движок рекомендаций: collaborative filtering + content-based                                      |
| **Wishlist**          | `Wishlist`, `WishlistItem`, `ShareLink`                                 | Списки желаемого, публичные ссылки для друзей                                                     |

> Все приложения изолированы как отдельные **Django apps** в каталоге [backend/apps/](backend/apps/). Зависимости между ними однонаправлены и проходят через сервисный слой, что облегчает рост системы и потенциальное выделение в микросервисы.

---

## 🐳 7. Сервисы в Docker Compose

`docker-compose.yml` поднимает **8 сервисов**, каждый со своим healthcheck и томом, где это необходимо.

| Сервис          | Образ / Сборка             | Порты      | Назначение                                                |
|-----------------|----------------------------|------------|-----------------------------------------------------------|
| `db`            | `postgres:15-alpine`       | `5432`     | Транзакционная БД (метаданные, заказы, пользователи)      |
| `redis`         | `redis:7-alpine`           | `6379`     | Кэш Django + брокер Celery + result backend               |
| `elasticsearch` | `elasticsearch:8.11.0`     | `9200`     | Полнотекстовый поиск, фасетные фильтры                    |
| `backend`       | `./backend/Dockerfile`     | `8000`     | Django + DRF + Gunicorn (миграции, collectstatic, gunicorn) |
| `celery_worker` | `./backend/Dockerfile`     | —          | Воркер фоновых задач (concurrency=4)                      |
| `celery_beat`   | `./backend/Dockerfile`     | —          | Планировщик cron-задач (DatabaseScheduler)                |
| `frontend`      | `./frontend/Dockerfile`    | `3000`     | React dev-server с hot reload                             |
| `nginx`         | `nginx:1.25-alpine`        | `80, 443`  | Reverse proxy, отдача static/media, SSL termination       |

**Тома:** `postgres_data`, `redis_data`, `es_data`, `static_volume`, `media_volume` — данные переживают пересоздание контейнеров.

---

## ⚡ 8. Быстрый старт (локально, Docker)

### Предварительные требования

- **Docker** и **Docker Compose v2.0+**
- **Git**
- Минимум **4 ГБ RAM**, свободные порты `3000`, `5432`, `6379`, `8000`, `9200`, `80`

### За 6 шагов

```bash
# 1. Клонируем репозиторий
git clone https://github.com/NodirOdilov/BookVerse.git
cd BookVerse

# 2. Создаём .env из шаблона и редактируем секреты
cp .env.example .env

# 3. Собираем образы
make build

# 4. Поднимаем все сервисы
make up

# 5. Применяем миграции и создаём суперпользователя
make migrate
make superuser

# 6. (Опционально) загружаем демо-данные и индексируем поиск
make seed
make reindex
```

После старта сервисы доступны по адресам:

| Что                 | URL                                          |
|---------------------|----------------------------------------------|
| 🌐 Frontend (SPA)   | <http://localhost:3000>                      |
| 🔌 REST API         | <http://localhost:8000/api/v1/>              |
| 🛡️ Django Admin     | <http://localhost:8000/admin/>               |
| 📖 OpenAPI / Swagger | <http://localhost:8000/api/v1/docs/>        |
| 🔍 Elasticsearch     | <http://localhost:9200>                     |
| 🌸 Flower (Celery)   | <http://localhost:5555> (после `make celery-flower`) |

---

## 🛠️ 9. Основные команды Makefile

> Все команды объединены в `Makefile` для единого опыта разработки. Полный список — `make help`.

### Docker

| Команда            | Действие                                          |
|--------------------|---------------------------------------------------|
| `make build`       | Собрать все Docker-образы                         |
| `make up`          | Запустить сервисы в фоне                          |
| `make down`        | Остановить и удалить контейнеры                   |
| `make restart`     | Перезапустить все сервисы                         |
| `make logs`        | Хвост логов всех контейнеров                      |
| `make logs-backend`| Логи только backend                               |
| `make logs-celery` | Логи Celery worker                                |
| `make ps`          | Список запущенных контейнеров                     |

### Backend / база

| Команда                | Действие                                       |
|------------------------|------------------------------------------------|
| `make shell`           | Django `shell_plus` (IPython)                  |
| `make dbshell`         | Прямой `psql` в БД                             |
| `make migrate`         | Применить миграции                             |
| `make makemigrations`  | Сгенерировать новые миграции                   |
| `make superuser`       | Создать суперпользователя                      |
| `make seed`            | Загрузить демо-фикстуры                        |
| `make flush`           | Полностью очистить БД (⚠️ destructive)         |
| `make collectstatic`   | Собрать статику                                |

### Тесты и качество

| Команда              | Действие                                         |
|----------------------|--------------------------------------------------|
| `make test`          | Backend-тесты через pytest                       |
| `make test-coverage` | Тесты с coverage-отчётом (HTML)                  |
| `make test-frontend` | Тесты React-приложения                           |
| `make test-all`      | Полный прогон backend + frontend                 |
| `make lint`          | flake8 + mypy + eslint                           |
| `make format`        | black + isort + prettier                         |
| `make check`         | Проверка форматирования без изменений            |

### Поиск, Celery, очистка

| Команда                | Действие                                       |
|------------------------|------------------------------------------------|
| `make reindex`         | Пересобрать индексы Elasticsearch              |
| `make celery-worker`   | Запустить воркер в foreground                  |
| `make celery-beat`     | Запустить планировщик в foreground             |
| `make celery-flower`   | Открыть Flower UI на :5555                     |
| `make clean`           | Очистить Python-кэш, pytest-кэш, coverage      |
| `make clean-docker`    | Удалить volumes и orphan-контейнеры            |
| `make clean-all`       | Полная очистка                                 |

---

## 🧪 10. Ручной запуск frontend и backend

Если по какой-то причине нужно поднять сервисы **без Docker** (например, для отладки в IDE):

### Backend

```bash
cd backend
python -m venv venv

# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

pip install -r requirements.txt

# .env должен указывать на локальные PostgreSQL / Redis / Elasticsearch
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Celery (в отдельном терминале)

```bash
cd backend
celery -A config worker -l info --concurrency=4
# и параллельно:
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

### Frontend

```bash
cd frontend
npm install
npm start
# REACT_APP_API_URL=http://localhost:8000/api/v1
```

---

## ⚙️ 11. Конфигурация и переменные окружения

Все секреты и настройки управляются через файл `.env` в корне проекта. Шаблон — `.env.example`.

| Переменная                  | Назначение                                | По умолчанию               |
|-----------------------------|-------------------------------------------|----------------------------|
| `DJANGO_SECRET_KEY`         | Секретный ключ Django                     | (генерируется)             |
| `DJANGO_DEBUG`              | Debug-режим                               | `True` (dev) / `False` (prod) |
| `DJANGO_ALLOWED_HOSTS`      | Разрешённые хосты                         | `localhost,127.0.0.1`      |
| `DJANGO_SETTINGS_MODULE`    | Профиль настроек                          | `config.settings.development` |
| `POSTGRES_DB`               | Имя БД                                    | `bookverse`                |
| `POSTGRES_USER`             | Пользователь БД                           | `bookverse`                |
| `POSTGRES_PASSWORD`         | Пароль БД                                 | `bookverse_secret`         |
| `DATABASE_URL`              | Connection string PostgreSQL              | см. `.env.example`         |
| `REDIS_URL`                 | Connection string Redis                   | `redis://redis:6379/0`     |
| `ELASTICSEARCH_URL`         | URL Elasticsearch                         | `http://elasticsearch:9200`|
| `CELERY_BROKER_URL`         | Брокер Celery                             | `redis://redis:6379/1`     |
| `CORS_ALLOWED_ORIGINS`      | Origins для CORS                          | `http://localhost:3000`    |
| `EMAIL_HOST`                | SMTP-сервер                               | `smtp.gmail.com`           |
| `EMAIL_HOST_USER`           | SMTP-логин                                | —                          |
| `EMAIL_HOST_PASSWORD`       | SMTP-пароль                               | —                          |
| `STRIPE_PUBLIC_KEY`         | Stripe publishable key                    | —                          |
| `STRIPE_SECRET_KEY`         | Stripe secret key                         | —                          |
| `STRIPE_WEBHOOK_SECRET`     | Подпись Stripe webhooks                   | —                          |
| `AWS_ACCESS_KEY_ID`         | Ключ S3-совместимого хранилища            | —                          |
| `AWS_SECRET_ACCESS_KEY`     | Секрет S3                                 | —                          |
| `AWS_STORAGE_BUCKET_NAME`   | Имя бакета для медиа                      | —                          |
| `SENTRY_DSN`                | DSN для Sentry                            | —                          |
| `REACT_APP_API_URL`         | Base URL API для фронтенда                | `http://localhost:8000/api/v1` |

> 🔒 **Никогда не коммитьте `.env`** — он в `.gitignore`. В production используйте секрет-менеджер (AWS Secrets Manager, Vault, Doppler).

---

## 🔌 12. API, очереди и интеграции

### REST API

BookVerse экспонирует версионированный REST API (`/api/v1/`) с авто-документацией через **drf-spectacular**:

- 📖 Swagger UI — <http://localhost:8000/api/v1/docs/>
- 📜 ReDoc — <http://localhost:8000/api/v1/redoc/>
- 🧾 OpenAPI JSON — <http://localhost:8000/api/v1/schema/>

#### Аутентификация (JWT)

```http
POST /api/v1/auth/token/
Content-Type: application/json

{
    "email": "user@example.com",
    "password": "your_password"
}
```

В ответ — пара `access` / `refresh` токенов. `access` отправляется в заголовке:

```http
Authorization: Bearer <access_token>
```

#### Ключевые эндпоинты

| Метод  | Эндпоинт                              | Описание                          |
|--------|---------------------------------------|-----------------------------------|
| `GET`  | `/api/v1/books/`                      | Список книг с фильтрами и пагинацией |
| `GET`  | `/api/v1/books/{isbn}/`               | Детальная страница книги          |
| `GET`  | `/api/v1/books/search/?q=...`         | Полнотекстовый поиск (Elasticsearch) |
| `GET`  | `/api/v1/authors/`                    | Список авторов                    |
| `GET`  | `/api/v1/catalog/featured/`           | Витрина «Featured»                |
| `GET`  | `/api/v1/catalog/bestsellers/`        | Бестселлеры                       |
| `POST` | `/api/v1/orders/`                     | Создать заказ                     |
| `POST` | `/api/v1/orders/{id}/checkout/`       | Stripe Checkout Session           |
| `GET`  | `/api/v1/reading/lists/`              | Списки чтения пользователя        |
| `POST` | `/api/v1/reading/progress/`           | Обновить прогресс                 |
| `GET`  | `/api/v1/reading/clubs/`              | Книжные клубы                     |
| `POST` | `/api/v1/reviews/`                    | Опубликовать отзыв                |
| `GET`  | `/api/v1/recommendations/`            | Персональные рекомендации         |
| `GET`  | `/api/v1/wishlist/`                   | Wishlist пользователя             |

### Очереди задач (Celery)

| Задача                          | Триггер                          | Что делает                                       |
|---------------------------------|----------------------------------|--------------------------------------------------|
| `send_order_confirmation_email` | После успешной оплаты            | Отправляет письмо с деталями заказа              |
| `rebuild_recommendations`       | Cron (раз в сутки)               | Пересчитывает матрицу схожести пользователей     |
| `reindex_books`                 | После save() книги (signal)      | Обновляет документ в Elasticsearch               |
| `refresh_bestsellers`           | Cron (раз в час)                 | Пересчитывает топ продаж за 24ч / 7д / 30д       |
| `clean_abandoned_carts`         | Cron (раз в сутки)               | Удаляет корзины старше 30 дней                   |
| `process_stripe_webhook`        | Webhook от Stripe                | Обрабатывает события платежей асинхронно         |

### Внешние интеграции

- **Stripe** — платежи, подписки, webhooks
- **SMTP / SendGrid** — транзакционные письма
- **AWS S3 / MinIO** — хранение обложек книг и аватаров
- **Sentry** — error tracking
- **Google OAuth / Facebook / GitHub** — social login через django-allauth

---

## 📊 13. Мониторинг и эксплуатация

### Health-checks

- `GET /health/` — агрегированная проверка (БД, Redis, кэш, миграции) через `django-health-check`
- В Docker Compose у каждого критичного сервиса свой `healthcheck` — `depends_on: { condition: service_healthy }` гарантирует правильный порядок старта

### Логирование

- Все сервисы пишут в stdout — собираются `docker compose logs` / Loki / CloudWatch / ELK
- Структурированный JSON-логгер для production (легко парсится агрегаторами)

### Метрики и трейсы

- **Sentry** — ошибки backend и frontend, с трейсами и breadcrumbs
- **Flower** (`make celery-flower`) — мониторинг очередей Celery в реальном времени
- **PostgreSQL slow query log** — анализ медленных запросов
- **Elasticsearch `/_cluster/health`** — состояние кластера

### Резервное копирование

- PostgreSQL: `pg_dump` + регулярные снимки тома `postgres_data`
- Медиа: репликация в S3-бакет
- Elasticsearch: snapshot repository в S3

---

## 🔁 14. CI/CD

Рекомендуемый pipeline (GitHub Actions / GitLab CI):

1. **Lint** — `make lint` (flake8, mypy, eslint)
2. **Format check** — `make check` (black, isort, prettier)
3. **Tests** — `make test-all` (backend + frontend)
4. **Coverage gate** — минимум 80% по `apps/`
5. **Security scan** — `pip-audit`, `npm audit`, Trivy для образов
6. **Build** — Docker-образы с тегом коммита и `latest`
7. **Push** — в Container Registry (GHCR / ECR / Docker Hub)
8. **Deploy** — `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` через SSH / ArgoCD / Kubernetes

> 💡 Pre-commit хуки запускают `black`, `isort` и `flake8` локально — обычно CI падает только на тестах.

---

## 🔐 15. Безопасность и работа с данными

| Аспект                  | Реализация                                                                              |
|-------------------------|-----------------------------------------------------------------------------------------|
| **Аутентификация**      | JWT (SimpleJWT) + refresh-токены, social-login через allauth                            |
| **Авторизация**         | DRF-permissions, object-level checks, role-based access в admin                          |
| **CORS**                | Whitelist через `CORS_ALLOWED_ORIGINS`                                                  |
| **CSRF**                | Включён для admin и форм; API защищён JWT                                               |
| **SQL Injection**       | ORM Django, никаких raw-запросов с конкатенацией                                        |
| **XSS**                 | Шаблоны Django + React автоматически экранируют, CSP-заголовки в Nginx                  |
| **Платежи**             | PCI DSS — карточные данные не касаются нашего сервера, всё через Stripe Elements        |
| **Секреты**             | Только в `.env` / секрет-менеджере, никогда в репозитории                               |
| **HTTPS**               | TLS termination в Nginx, HSTS включён в production                                      |
| **Rate limiting**       | django-ratelimit + Nginx `limit_req_zone` для критичных эндпоинтов                      |
| **Загрузка файлов**     | Валидация MIME, ограничение размера, антивирусная проверка для аватаров                 |
| **Хранение паролей**    | PBKDF2 (Django default), миграция на argon2 по необходимости                            |
| **Аудит**               | Логирование критичных действий: смена пароля, оформление заказа, удаление аккаунта      |

---

## 🎭 16. Роли компонентов в продакшене

| Компонент          | Роль в production                                                                              |
|--------------------|------------------------------------------------------------------------------------------------|
| **Nginx**          | TLS termination, статика, балансировка, rate limiting, gzip, кэширование                       |
| **Gunicorn**       | WSGI-сервер Django: 4 worker × 2 thread (тюнится под нагрузку)                                  |
| **Django + DRF**   | Бизнес-логика, валидация, авторизация, OpenAPI                                                  |
| **PostgreSQL**     | Source of truth: пользователи, заказы, книги, отзывы                                            |
| **Redis**          | Кэш горячих данных (списки книг, рейтинги), брокер Celery, sessions, rate-limit counters        |
| **Elasticsearch**  | Поиск, фильтрация, автодополнение, фасеты                                                       |
| **Celery Worker**  | Email-рассылки, реиндексация, пересчёт рекомендаций, обработка Stripe webhooks                  |
| **Celery Beat**    | Cron-задачи: бестселлеры, очистка корзин, daily digests                                         |
| **React SPA**      | UI, маршрутизация, локальное состояние через Redux Toolkit                                      |
| **Stripe**         | Внешняя система платежей и подписок                                                             |
| **S3 / MinIO**     | Хранение обложек, аватаров, статических ассетов                                                 |
| **Sentry**         | Сбор ошибок и performance traces                                                                |

---

## 📄 17. Лицензия

Проект распространяется под лицензией **MIT** — свободно для коммерческого и некоммерческого использования. Полный текст — в файле [LICENSE](LICENSE).

---

## 💬 18. Поддержка

- 🐛 **Баги и фичи** — [GitHub Issues](https://github.com/NodirOdilov/BookVerse/issues)
- 💡 **Идеи и обсуждения** — [GitHub Discussions](https://github.com/NodirOdilov/BookVerse/discussions)
- 🤝 **Контрибьюции** — форк → ветка `feature/your-feature` → PR с описанием
- 📧 **Контакт автора** — [Nodir Odilov](https://github.com/NodirOdilov)

---

<div align="center">

**📚 BookVerse — читай. собирай. рекомендуй. покупай.**

⭐ Поставьте звезду, если проект оказался полезен!

</div>
