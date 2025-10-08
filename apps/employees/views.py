import logging

from django.shortcuts import render

from apps.core.decorators import smart_auth
from .services import EmployeeService

logger = logging.getLogger(__name__)


@smart_auth
def index(request):
    try:
        service = EmployeeService(request.bitrix_user_token)
        employees_data = service.get_employees_data()
        context = {"employees": employees_data}
        logger.info("Получены данные о сотрудниках и иерархии (batch)")
        return render(request, "employees/index.html", context)

    except Exception as e:
        logger.error("Ошибка при получении данных сотрудников: %s", str(e))
        return render(request, "employees/error.html", {"error": str(e)})
