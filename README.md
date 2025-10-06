# Bitrix24 Apps

Django проект с локальными приложениями для Bitrix24.

## Приложения

### Home (apps/home/)
Главная страница с выбором доступных приложений.

**Функциональность:**
- Отображение приветствия с именем пользователя
- Визуальная карточка каждого приложения с описанием
- Навигация между приложениями

### Deal Management (apps/deals/)
Управление сделками через iframe приложение.

**Функциональность:**
- Авторизация пользователя через Bitrix24
- Отображение имени текущего пользователя
- Список 10 последних активных сделок с локализованными стадиями
- Создание новой сделки с кастомным полем "Источник лида"
- Автоматический перевод стадий сделок на русский язык

### Product QR Generator (apps/product_qr/)
Генерация QR-кодов для товаров с публичными секретными ссылками.

**Функциональность:**
- Генерация QR-кодов для товаров из Bitrix24
- Создание публичных страниц товаров без авторизации
- Секретные непредсказуемые URL на основе UUID4
- Возможность создания нескольких QR-кодов для одного товара
- Автоматическое извлечение изображений товара из разных полей
- Скачивание QR-кодов в формате PNG
- Сохранение данных товара для доступа без авторизации

### Employee Hierarchy (apps/employees/)
Отображение иерархии сотрудников и статистики по звонкам.

**Функциональность:**
- Отображение таблицы всех активных сотрудников компании.
- Построение и вывод полной цепочки руководителей для каждого сотрудника.
- Подсчет и отображение количества исходящих звонков (>60 секунд) за последние 24 часа.
- Интеграция с Bitrix24 JS SDK для открытия профиля сотрудника в слайдере по клику.

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
- **qrcode[pil] 7.4.2** - генерация QR-кодов с поддержкой изображений

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

# Bitrix24 Webhook (для публичного доступа к товарам)
BITRIX_WEBHOOK_URL=https://your-domain.bitrix24.ru/rest/1/webhook_key/
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

### Создание входящего webhook

Для публичного доступа к товарам необходим входящий webhook:

1. Перейдите в Bitrix24: Разработчикам → Другое → Входящий вебхук
2. Создайте новый webhook
3. Выберите права доступа: CRM (чтение)
4. Скопируйте URL вебхука (например, `https://your-domain.bitrix24.ru/rest/1/webhook_key/`)
5. Обновите переменную `BITRIX_WEBHOOK_URL` в `.env`

## Структура проекта

```
deal_management/
├── config/              # Настройки Django
│   ├── settings.py
│   ├── urls.py
│   ├── middleware.py    # Кастомные middleware (ngrok warning bypass)
│   └── wsgi.py
├── apps/                # Django приложения
│   ├── home/            # Главная страница с выбором приложений
│   ├── deals/           # Управление сделками
│   ├── product_qr/      # QR-коды для товаров
│   └── employees/       # Иерархия сотрудников
├── templates/           # HTML шаблоны
│   ├── base.html
│   ├── home/
│   ├── deals/
│   ├── product_qr/
│   └── employees/
├── static/              # Статические файлы
├── integration_utils/   # Submodule для работы с Bitrix24
├── .env
├── .env.example
├── manage.py
└── requirements.txt
```

## Технические детали

### Авторизация

Приложение использует кастомный декоратор `smart_auth`, который автоматически выбирает метод авторизации:

- При первом открытии (GET с `AUTH_ID`) - авторизация через Bitrix24
- При последующих запросах - авторизация через cookie

### Используемые API методы Bitrix24

**Авторизованные запросы (через OAuth):**
- `user.current` - получение информации о текущем пользователе
- `crm.deal.list` - получение списка сделок с фильтрацией и сортировкой
- `crm.deal.add` - создание новой сделки
- `crm.product.get` - получение информации о товаре с сохранением в БД

**Публичные запросы (через webhook):**
- `crm.product.get` - получение информации о товаре для публичной страницы

### Template Filters

Приложение использует кастомный template filter для локализации стадий сделок:

**`deals/templatetags/deal_filters.py`:**
- `translate_stage` - переводит технические ID стадий (NEW, EXECUTING) на русский язык

Использование в шаблоне:
```django
{% load deal_filters %}
{{ deal.STAGE_ID|translate_stage }}
```

### Модель ProductQR

Приложение использует модель для хранения информации о QR-кодах:

```python
class ProductQR(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4)
    product_id = models.CharField(max_length=50)
    member_id = models.CharField(max_length=50)
    product_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
```

- `uuid` - уникальный идентификатор для секретного URL
- `product_id` - ID товара в Bitrix24
- `member_id` - ID портала Bitrix24
- `product_data` - полные данные товара (JSON) для доступа без авторизации
- `created_at` - дата создания QR-кода

### Генерация QR-кодов

Приложение использует библиотеку `qrcode` для генерации QR-кодов:

- Формат: PNG
- Кодировка: Base64 для встраивания в HTML
- Публичный URL: `https://your-domain.ngrok-free.app/qr/view/{uuid}/`
- UUID генерируется автоматически при создании записи

### Middleware

**NgrokSkipWarningMiddleware** (`config/middleware.py`):
- Автоматически добавляет заголовок для обхода warning страницы ngrok
- Позволяет открывать приложение в iframe без дополнительных действий

### Безопасность

Приложение использует отдельные ключи для разных целей:
- `SECRET_KEY` - Django secret key для сессий и CSRF
- `BITRIX_SALT` - уникальный salt для криптографических операций Bitrix24

### Логирование

Настроены следующие логгеры:

- **apps** - логирование приложений с уровнем INFO
- **integration_utils** - логирование Bitrix24 интеграции с уровнем WARNING (избегаем избыточных INFO логов)

Все ошибки логируются с уровнем ERROR и выводятся в консоль.

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

### QR-код не открывает страницу товара

Проверьте:
- URL ngrok актуален и доступен извне
- Переменная `NGROK_URL` в `.env` обновлена
- Домен ngrok добавлен в `ALLOWED_HOSTS` и `CSRF_TRUSTED_ORIGINS`
- Webhook `BITRIX_WEBHOOK_URL` настроен корректно

### Публичная страница товара не загружается

Убедитесь что:
- Webhook имеет права на чтение CRM
- В модели ProductQR сохранены данные товара (`product_data`)
- UUID в URL корректный и существует в базе данных

### Изображения товара не отображаются

Приложение ищет изображения в следующем порядке:
1. `PREVIEW_PICTURE` - основное изображение
2. `DETAIL_PICTURE` - детальное изображение
3. `PROPERTY_*` - кастомные поля с типом файл

Если изображения не отображаются, проверьте что они загружены в карточку товара в Bitrix24.

## Лицензия

MIT
