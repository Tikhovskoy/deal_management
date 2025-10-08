import json
import logging

from django.shortcuts import render

from apps.core.decorators import smart_auth
from .services import CompaniesMapService

logger = logging.getLogger(__name__)


@smart_auth
def index(request):
    try:
        service = CompaniesMapService(request.bitrix_user_token)
        companies_data, yandex_api_key = service.get_companies_data()

        context = {
            "yandex_api_key": yandex_api_key,
            "companies_json": json.dumps(companies_data),
        }
        return render(request, "companies_map/index.html", context)

    except Exception as e:
        logger.error(f"Ошибка при получении данных для карты: {e}")
        return render(request, "companies_map/index.html", {"error": str(e)})
