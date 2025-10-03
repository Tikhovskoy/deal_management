from django.shortcuts import render
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
import logging

logger = logging.getLogger(__name__)


@main_auth(on_start=True, set_cookie=True)
def index(request):
    try:
        user = request.bitrix_user_token.call_api_method('user.current')
        user_name = user.get('result', {}).get('NAME', 'Неизвестно')

        context = {
            'user_name': user_name,
            'user_data': user.get('result', {}),
        }

        logger.info(f"Получены данные пользователя: {user_name}")
        return render(request, 'deals/index.html', context)

    except Exception as e:
        logger.error(f"Ошибка при получении данных пользователя: {str(e)}")
        context = {
            'error': str(e)
        }
        return render(request, 'deals/error.html', context)
