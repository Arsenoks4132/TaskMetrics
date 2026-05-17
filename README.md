# TaskAndTimes

Клиент-серверное приложение для управления задачами и учёта рабочего времени сотрудников, разработанное на фреймворке Django.

## Функциональность

- **Сотрудник** может регистрироваться, добавлять, редактировать и удалять свои рабочие задачи, редактировать профиль и менять пароль.
- **Руководитель** может просматривать статистику всех сотрудников, редактировать и удалять задачи любого сотрудника, управлять категориями задач (создание, редактирование, удаление).
- Ролевая модель: разграничение доступа через флаг `is_staff` Django.
- Кэширование страниц через Redis.
- Валидация паролей (минимальная длина 8 символов, проверка на простоту).

## Структура проекта

```
TaskMetrics/
├── docker/                        # Конфигурации контейнеров
│   ├── django/
│   │   ├── Dockerfile             # Образ Django-приложения (Python 3.12)
│   │   └── entrypoint.sh          # Скрипт запуска: миграции, фикстуры, Gunicorn
│   ├── nginx/
│   │   └── TaskAndTime.conf       # Конфигурация Nginx (статика + проксирование)
│   └── traefik/
│       ├── traefik.yml            # Точки входа Traefik
│       └── dynamic.yml            # Динамическая маршрутизация Traefik
│
├── TaskAndTime/                   # Django-проект
│   ├── manage.py
│   ├── initial_fixture.json       # Начальные данные (категории, пользователи)
│   │
│   ├── TaskAndTime/               # Настройки проекта
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── wsgi.py
│   │   └── asgi.py
│   │
│   ├── Tasks/                     # Основное приложение
│   │   ├── models.py              # Модели: User, Category, Task
│   │   ├── views.py               # CBV: профиль, статистика, CRUD задач и категорий
│   │   ├── urls.py                # URL-маршруты
│   │   ├── forms.py               # Формы: регистрация, задача, профиль, категория
│   │   ├── admin.py               # Регистрация моделей в Django Admin
│   │   ├── tests.py               # Фаззинг-тесты (Hypothesis)
│   │   ├── migrations/            # Миграции базы данных
│   │   ├── templatetags/
│   │   │   └── Tasks_tags.py      # Тег post_form для рендеринга форм
│   │   └── templates/Tasks/       # HTML-шаблоны
│   │       ├── index.html         # Главная страница
│   │       ├── login.html         # Страница авторизации
│   │       ├── profile.html       # Профиль сотрудника + список задач
│   │       ├── edit_profile.html  # Редактирование профиля
│   │       ├── change_password.html # Смена пароля
│   │       ├── statistics.html    # Статистика сотрудников (руководитель)
│   │       ├── tasks_list.html    # Список задач сотрудника (руководитель)
│   │       ├── edit_task.html     # Редактирование задачи
│   │       ├── delete_task.html   # Подтверждение удаления задачи
│   │       ├── categories.html    # Список категорий (руководитель)
│   │       ├── category_form.html # Создание/редактирование категории
│   │       ├── delete_category.html # Подтверждение удаления категории
│   │       ├── page403.html       # Страница 403
│   │       └── page404.html       # Страница 404
│   │
│   ├── templates/
│   │   ├── base.html              # Базовый шаблон
│   │   └── form.html              # Универсальный шаблон формы
│   │
│   └── static/Tasks/
│       └── css/styles.css         # Стили приложения
│
├── docker-compose.yaml            # Оркестрация: Django × 3, Nginx × 3, PostgreSQL, Redis, Traefik
├── requirements.txt               # Python-зависимости
└── .env                           # Переменные окружения (не включается в репозиторий)
```

## Архитектура

Запросы проходят по следующей цепочке:

```
Браузер :80  →  Traefik  →  Nginx (×3)
                                ├── статика/медиа — отдаётся напрямую
                                └── динамика → Traefik → Gunicorn/Django (×3) → PostgreSQL
                                                                           └── Redis (кэш)
```

## Технологический стек

| Компонент | Технология |
|---|---|
| Backend | Django 5.1, Gunicorn |
| База данных | PostgreSQL 17 |
| Кэш | Redis |
| Веб-сервер | Nginx 1.27 |
| Балансировщик | Traefik v3.2 |
| Контейнеризация | Docker, Docker Compose |
| Тестирование | Django TestCase + Hypothesis (fuzz) |

## Запуск

### Требования

- Docker и Docker Compose
- Заполненный файл `.env` (см. `.env.example`)

### Переменные окружения (`.env`)

```
DJANGO_SECRET_KEY=your-secret-key
HOST_IP=your-server-ip

POSTGRES_DB=taskandtimes
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-db-password
POSTGRES_HOST=postgres_db

REDIS_CACHE_HOST=redis_cache
```

### Запуск контейнеров

```bash
docker compose up -d --build
```

Приложение будет доступно по адресу `http://localhost`.

При первом запуске автоматически выполняются миграции и загружаются начальные данные из `initial_fixture.json` (демо-пользователи и категории задач).

### Запуск тестов (локально)

```bash
cd TaskAndTime
pip install -r ../requirements.txt
python manage.py test Tasks
```

## Демо-пользователи (из фикстуры)

| Роль | Логин | Пароль |
|---|---|---|
| Руководитель | `manager_demo` | `manager_demo` |
| Сотрудник | `employee_demo` | `employee_demo` |

> После запуска рекомендуется сменить пароли через интерфейс приложения.
