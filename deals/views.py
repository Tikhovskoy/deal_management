from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from functools import wraps
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)

CUSTOM_FIELD_NAME = os.getenv('CUSTOM_FIELD_NAME', 'UF_CRM_1759500436')
DEFAULT_STAGE = os.getenv('DEFAULT_STAGE', 'NEW')
DEFAULT_CURRENCY = os.getenv('DEFAULT_CURRENCY', 'RUB')


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
    success_message = None
    error_message = None

    try:
        if request.method == 'POST':
            title = request.POST.get('title', '').strip()
            custom_field = request.POST.get(CUSTOM_FIELD_NAME, '').strip()
            opportunity = request.POST.get('opportunity', '').strip()

            logger.info(f"Form data: title={title}, source={custom_field}, amount={opportunity}")

            if not title:
                error_message = 'Название сделки обязательно'
            elif not custom_field:
                error_message = 'Источник лида обязателен'
            else:
                fields = {
                    'TITLE': title,
                    'STAGE_ID': DEFAULT_STAGE,
                    CUSTOM_FIELD_NAME: custom_field,
                    'CURRENCY_ID': DEFAULT_CURRENCY
                }

                if opportunity:
                    try:
                        fields['OPPORTUNITY'] = float(opportunity)
                    except ValueError:
                        error_message = 'Сумма должна быть числом'

                if not error_message:
                    logger.info(f"Отправка данных в Bitrix24: {fields}")
                    response = request.bitrix_user_token.call_api_method(
                        'crm.deal.add',
                        {'fields': fields}
                    )

                    logger.info(f"Bitrix24 response: {response}")

                    if 'error' in response:
                        logger.error(f"Bitrix24 error: {response['error']}")
                        error_message = f"Ошибка Bitrix24: {response['error'].get('error_description', 'Неизвестная ошибка')}"
                    elif response.get('result'):
                        deal_id = response['result']
                        success_message = f'Сделка #{deal_id} успешно создана!'
                        logger.info(f"Создана сделка #{deal_id}")
                    else:
                        error_message = 'Ошибка при создании сделки'
                        logger.error(f"Ошибка создания сделки: {response}")

        user = request.bitrix_user_token.call_api_method('user.current')
        user_name = user.get('result', {}).get('NAME', 'Неизвестно')

        deals_response = request.bitrix_user_token.call_api_method(
            'crm.deal.list',
            {
                'order': {'DATE_CREATE': 'DESC'},
                'filter': {'CLOSED': 'N'},
                'select': ['ID', 'TITLE', 'STAGE_ID', 'OPPORTUNITY', 'CURRENCY_ID']
            }
        )

        deals = deals_response.get('result', [])[:10]

        context = {
            'user_name': user_name,
            'deals': deals,
            'success_message': success_message,
            'error_message': error_message,
            'custom_field_name': CUSTOM_FIELD_NAME,
        }

        logger.info(f"Получены данные пользователя: {user_name}")
        logger.info(f"Получено сделок: {len(deals)}")
        return render(request, 'deals/index.html', context)

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        error_str = str(e)

        if 'expired_token' in error_str:
            context = {
                'error': 'Срок действия токена истек. Пожалуйста, обновите страницу или откройте приложение заново.'
            }
        else:
            context = {
                'error': 'Произошла ошибка при работе с Bitrix24. Попробуйте обновить страницу.'
            }
        return render(request, 'deals/error.html', context)
