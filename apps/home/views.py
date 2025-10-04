from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from functools import wraps


def smart_auth(func):
    @csrf_exempt
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        has_auth_id = request.POST.get('AUTH_ID') or request.GET.get('AUTH_ID')

        if has_auth_id:
            return main_auth(on_start=True, set_cookie=True)(func)(request, *args, **kwargs)
        else:
            return main_auth(on_cookies=True, set_cookie=True)(func)(request, *args, **kwargs)
    return wrapper


@smart_auth
def index(request):
    apps = [
        {
            'title': 'Управление сделками',
            'description': 'Просмотр и создание сделок Bitrix24',
            'icon': '📋',
            'url': '/deals/',
            'color': '#28a745'
        },
        {
            'title': 'QR-коды товаров',
            'description': 'Генерация QR-кодов для товаров',
            'icon': '📱',
            'url': '/qr/',
            'color': '#007bff'
        }
    ]

    context = {
        'apps': apps
    }

    return render(request, 'home/index.html', context)
