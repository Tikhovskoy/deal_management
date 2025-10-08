from django.shortcuts import render
from django.urls import reverse

from apps.core.decorators import smart_auth


@smart_auth
def index(request):
    user_data = request.bitrix_user_token.call_api_method("user.current")
    user_name = user_data.get("result", {}).get("NAME", "Пользователь")

    apps = [
        {
            "title": "Управление сделками",
            "description": "Просмотр и создание сделок Bitrix24",
            "icon": "📋",
            "url": reverse("deals:index"),
            "color": "#28a745",
        },
        {
            "title": "QR-коды товаров",
            "description": "Генерация QR-кодов для товаров",
            "icon": "📱",
            "url": reverse("product_qr:index"),
            "color": "#007bff",
        },
        {
            "title": "Иерархия сотрудников",
            "description": "Структура компании и статистика звонков",
            "icon": "👥",
            "url": reverse("employees:index"),
            "color": "#6f42c1",
        },
        {
            "title": "Карта компаний",
            "description": "Отображение адресов компаний на Яндекс-карте",
            "icon": "🗺️",
            "url": reverse("companies_map:index"),
            "color": "#fd7e14",
        },
        {
            "title": "Менеджер контактов",
            "description": "Импорт и экспорт контактов из CSV/XLSX",
            "icon": "📇",
            "url": reverse("contact_manager:index"),
            "color": "#17a2b8",
        },
    ]

    context = {"apps": apps, "user_name": user_name}

    return render(request, "home/index.html", context)
