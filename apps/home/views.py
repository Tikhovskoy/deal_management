from django.shortcuts import render


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
