from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from functools import wraps
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


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


def get_department_heads(departments):
    department_heads = {}
    for dept in departments:
        dept_id = dept.get('ID')
        head_id = dept.get('UF_HEAD')
        if dept_id and head_id:
            department_heads[int(dept_id)] = int(head_id)
    return department_heads


def build_manager_chain(user, users_by_id, department_heads):
    managers = []
    user_departments = user.get('UF_DEPARTMENT', [])

    if not user_departments:
        return managers

    primary_dept = user_departments[0] if user_departments else None
    if not primary_dept:
        return managers

    visited_depts = set()
    current_dept = int(primary_dept)

    while current_dept and current_dept not in visited_depts:
        visited_depts.add(current_dept)

        head_id = department_heads.get(current_dept)
        if not head_id:
            break

        manager = users_by_id.get(head_id)
        if manager and manager.get('ID') != user.get('ID'):
            managers.append(manager)

            manager_depts = manager.get('UF_DEPARTMENT', [])
            current_dept = int(manager_depts[0]) if manager_depts else None
        else:
            break

    return managers


def get_calls_statistics(bitrix_token, users):
    user_calls = {}
    for user in users:
        user_calls[user['ID']] = 0

    try:
        now = datetime.now()
        date_from = now - timedelta(hours=24)

        filter_params = {
            'FILTER': {
                '>=CALL_START_DATE': date_from.strftime('%Y-%m-%d %H:%M:%S'),
                'CALL_TYPE': 2
            }
        }

        calls_response = bitrix_token.call_api_method('voximplant.statistic.get', filter_params)
        calls = calls_response.get('result', [])

        for call in calls:
            duration = int(call.get('CALL_DURATION', 0))
            portal_user_id = call.get('PORTAL_USER_ID')

            if duration > 60 and portal_user_id:
                user_id = str(portal_user_id)
                if user_id in user_calls:
                    user_calls[user_id] += 1

        logger.info("Получена статистика звонков для %d пользователей", len(user_calls))
        return user_calls

    except Exception as e:
        logger.error("Ошибка при получении статистики звонков: %s", str(e))
        return user_calls


@smart_auth
def index(request):
    try:
        users_response = request.bitrix_user_token.call_api_method('user.get', {
            'filter': {'ACTIVE': True},
            'select': ['ID', 'NAME', 'LAST_NAME', 'SECOND_NAME', 'UF_DEPARTMENT']
        })

        users = users_response.get('result', [])

        departments_response = request.bitrix_user_token.call_api_method('department.get', {})
        departments = departments_response.get('result', [])

        department_heads = get_department_heads(departments)
        users_by_id = {int(user['ID']): user for user in users}

        user_calls = get_calls_statistics(request.bitrix_user_token, users)

        employees_data = []
        for user in users:
            full_name = f"{user.get('LAST_NAME', '')} {user.get('NAME', '')} {user.get('SECOND_NAME', '')}".strip()

            managers = build_manager_chain(user, users_by_id, department_heads)
            managers_names = [f"{m.get('LAST_NAME', '')} {m.get('NAME', '')}".strip() for m in managers]

            employees_data.append({
                'id': user.get('ID'),
                'name': full_name,
                'managers': managers_names,
                'calls_count': user_calls.get(user.get('ID'), 0)
            })

        context = {
            'employees': employees_data
        }

        logger.info("Получены данные о сотрудниках и иерархии")
        return render(request, 'employees/index.html', context)

    except Exception as e:
        logger.error("Ошибка при получении данных сотрудников: %s", str(e))
        return render(request, 'employees/error.html', {'error': str(e)})
