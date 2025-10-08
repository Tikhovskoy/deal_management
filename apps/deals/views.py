import logging

from django.shortcuts import render
from django.conf import settings

from apps.core.decorators import smart_auth

logger = logging.getLogger(__name__)


@smart_auth
def index(request):
    success_message = None
    error_message = None

    try:
        if request.method == "POST":
            title = request.POST.get("title", "").strip()
            custom_field = request.POST.get(settings.CUSTOM_FIELD_NAME, "").strip()
            opportunity = request.POST.get("opportunity", "").strip()

            logger.info(
                f"Form data: title={title}, source={custom_field}, amount={opportunity}"
            )

            if not title:
                error_message = "Название сделки обязательно"
            elif not custom_field:
                error_message = "Источник лида обязателен"
            else:
                fields = {
                    "TITLE": title,
                    "STAGE_ID": settings.DEFAULT_STAGE,
                    settings.CUSTOM_FIELD_NAME: custom_field,
                    "CURRENCY_ID": settings.DEFAULT_CURRENCY,
                }

                if opportunity:
                    try:
                        fields["OPPORTUNITY"] = float(opportunity)
                    except ValueError:
                        error_message = "Сумма должна быть числом"

                if not error_message:
                    logger.info(f"Отправка данных в Bitrix24: {fields}")
                    response = request.bitrix_user_token.call_api_method(
                        "crm.deal.add", {"fields": fields}
                    )

                    logger.info(f"Bitrix24 response: {response}")

                    if "error" in response:
                        logger.error(f"Bitrix24 error: {response['error']}")
                        error_message = f"Ошибка Bitrix24: {response['error'].get('error_description', 'Неизвестная ошибка')}"
                    elif response.get("result"):
                        deal_id = response["result"]
                        success_message = f"Сделка #{deal_id} успешно создана!"
                        logger.info(f"Создана сделка #{deal_id}")
                    else:
                        error_message = "Ошибка при создании сделки"
                        logger.error(f"Ошибка создания сделки: {response}")

        user = request.bitrix_user_token.call_api_method("user.current")
        user_name = user.get("result", {}).get("NAME", "Неизвестно")

        deals_response = request.bitrix_user_token.call_api_method(
            "crm.deal.list",
            {
                "order": {"DATE_CREATE": "DESC"},
                "filter": {"CLOSED": "N"},
                "select": ["ID", "TITLE", "STAGE_ID", "OPPORTUNITY", "CURRENCY_ID"],
            },
        )

        deals = deals_response.get("result", [])[:10]

        lead_source_options = []
        try:
            fields_response = request.bitrix_user_token.call_api_method(
                "crm.deal.fields"
            )
            if "result" in fields_response:
                all_fields = fields_response["result"]
                custom_field_data = all_fields.get(settings.CUSTOM_FIELD_NAME)
                if custom_field_data and custom_field_data.get("items"):
                    lead_source_options = custom_field_data["items"]
                else:
                    logger.warning(
                        f"Custom field {settings.CUSTOM_FIELD_NAME} not found or has no items."
                    )
                    if not error_message:
                        error_message = (
                            f"Не удалось найти кастомное поле {settings.CUSTOM_FIELD_NAME}."
                        )
            else:
                logger.error(
                    f"Failed to get deal fields: {fields_response.get('error_description')}"
                )
                if not error_message:
                    error_message = "Не удалось загрузить описание полей сделки."

        except Exception as e:
            logger.error(f"Could not fetch lead source options: {e}")
            if not error_message:
                error_message = "Не удалось загрузить опции для поля 'Источник лида'."

        context = {
            "user_name": user_name,
            "deals": deals,
            "success_message": success_message,
            "error_message": error_message,
            "custom_field_name": settings.CUSTOM_FIELD_NAME,
            "lead_source_options": lead_source_options,
        }

        logger.info(f"Получены данные пользователя: {user_name}")
        logger.info(f"Получено сделок: {len(deals)}")
        return render(request, "deals/index.html", context)

    except Exception as e:
        logger.error(f"Ошибка при получении данных: {str(e)}")
        error_str = str(e)

        if "expired_token" in error_str:
            context = {
                "error": "Срок действия токена истек. Пожалуйста, обновите страницу или откройте приложение заново."
            }
        else:
            context = {
                "error": "Произошла ошибка при работе с Bitrix24. Попробуйте обновить страницу."
            }
        return render(request, "deals/error.html", context)
