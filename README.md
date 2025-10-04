# Bitrix24 Deal Management

Django-приложение для управления сделками Bitrix24 через iframe.

## Функциональность

- Авторизация пользователя через Bitrix24
- Отображение имени текущего пользователя
- Список 10 последних активных сделок с локализованными стадиями
- Создание новой сделки с кастомным полем "Источник лида"
- Автоматический перевод стадий сделок на русский язык

## Требования

- Python 3.12+
- PostgreSQL 12+
- ngrok (для локальной разработки)
- Bitrix24 аккаунт с правами на создание локальных приложений

## Зависимости

- **Django 4.2** - веб-фреймворк
- **psycopg-binary 3.2.10** - PostgreSQL драйвер (psycopg3)
- **python-dotenv 1.0.0** - управление переменными окружения
- **requests 2.31.0** - HTTP библиотека для API запросов
- **django-prettyjson 0.4.1** - виджет для отображения JSON в Django Admin

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository-url>
cd deal_management
git submodule update --init --recursive
```

### 2. Создание виртуального окружения

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Установка зависимостей

```bash
pip install -r requirements.txt
```

### 4. Настройка базы данных

Создайте базу данных PostgreSQL:

```sql
CREATE DATABASE bitrix_deals;
```

### 5. Настройка переменных окружения

Скопируйте `.env.example` в `.env` и заполните необходимые значения:

```bash
cp .env.example .env
```

Обязательные переменные:

```env
# Bitrix24
CLIENT_ID=your_client_id
CLIENT_SECRET=your_client_secret
DOMAIN=your-domain.bitrix24.ru
BITRIX_SALT=your-unique-salt-here  # Генерируется через: python -c "import secrets; print(secrets.token_urlsafe(50))"

# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,your-ngrok-domain.ngrok-free.app

# Database
DATABASE_NAME=bitrix_deals
DATABASE_USER=postgres
DATABASE_PASSWORD=your_password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# ngrok
NGROK_URL=your-ngrok-domain.ngrok-free.app

# Bitrix24 Settings
CUSTOM_FIELD_NAME=UF_CRM_1759500436
DEFAULT_STAGE=NEW
DEFAULT_CURRENCY=RUB
```

**Генерация BITRIX_SALT:**

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 6. Применение миграций

```bash
python manage.py migrate
```

### 7. Запуск сервера

```bash
python manage.py runserver
```

### 8. Настройка ngrok

В отдельном терминале запустите ngrok:

```bash
ngrok http 8000
```

Скопируйте HTTPS URL и обновите переменные `NGROK_URL` и `ALLOWED_HOSTS` в `.env`.

## Настройка Bitrix24

### Создание локального приложения

1. Перейдите в Bitrix24: Разработчикам → Другое → Локальные приложения
2. Создайте новое приложение
3. Укажите URL приложения: `https://your-ngrok-domain.ngrok-free.app/`
4. Сохраните `CLIENT_ID` и `CLIENT_SECRET` в `.env`

### Создание кастомного поля

1. Перейдите в CRM → Настройки → Настройка полей → Сделки
2. Создайте поле типа "Список" с названием "Источник лида"
3. Добавьте варианты: Сайт, Телефон, Email, Реклама
4. Скопируйте символьный код поля (например, `UF_CRM_1759500436`)
5. Обновите переменную `CUSTOM_FIELD_NAME` в `.env`

## Структура проекта

```
deal_management/
├── config/              # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── deals/               # Основное приложение
│   ├── views.py
│   ├── urls.py
│   └── templatetags/    # Кастомные template filters
│       ├── __init__.py
│       └── deal_filters.py  # Фильтр для перевода стадий
├── templates/           # HTML шаблоны
│   └── deals/
│       ├── index.html
│       └── error.html
├── integration_utils/   # Submodule для работы с Bitrix24
├── .env                 # Переменные окружения (не в git)
├── .env.example         # Пример переменных окружения
├── manage.py
└── requirements.txt
```

## Технические детали

### Авторизация

Приложение использует кастомный декоратор `smart_auth`, который автоматически выбирает метод авторизации:

- При первом открытии (GET с `AUTH_ID`) - авторизация через Bitrix24
- При последующих запросах - авторизация через cookie

### Используемые API методы Bitrix24

- `user.current` - получение информации о текущем пользователе
- `crm.deal.list` - получение списка сделок с фильтрацией и сортировкой
- `crm.deal.add` - создание новой сделки

### Template Filters

Приложение использует кастомный template filter для локализации стадий сделок:

**`deals/templatetags/deal_filters.py`:**
- `translate_stage` - переводит технические ID стадий (NEW, EXECUTING) на русский язык

Использование в шаблоне:
```django
{% load deal_filters %}
{{ deal.STAGE_ID|translate_stage }}
```

### Безопасность

Приложение использует отдельные ключи для разных целей:
- `SECRET_KEY` - Django secret key для сессий и CSRF
- `BITRIX_SALT` - уникальный salt для криптографических операций Bitrix24

### Логирование

Все операции с Bitrix24 API логируются в консоль с уровнем INFO. Ошибки логируются с уровнем ERROR.

## Устранение неполадок

### Ошибка 403 Forbidden

Проверьте настройки:
- Домен Bitrix24 добавлен в `CSRF_TRUSTED_ORIGINS`
- Cookie включены в браузере
- URL приложения корректен в настройках Bitrix24

### Приложение не открывается в Bitrix24

Убедитесь что:
- ngrok запущен и URL актуален
- URL в настройках приложения Bitrix24 совпадает с ngrok URL
- Домен ngrok добавлен в `ALLOWED_HOSTS`

### Expired token

При истечении токена закройте и откройте приложение заново в Bitrix24 для получения нового токена.

### Кастомное поле не сохраняется

Проверьте:
- Поле создано в Bitrix24
- Символьный код поля указан корректно в `CUSTOM_FIELD_NAME`
- Значения опций соответствуют ID из списка Bitrix24

### Отсутствует BITRIX_SALT

Если в `.env` не указан `BITRIX_SALT`, приложение использует `SECRET_KEY` (fallback для обратной совместимости). Для продакшена рекомендуется создать отдельный `BITRIX_SALT`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

## Лицензия

MIT
