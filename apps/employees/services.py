import logging
from datetime import timedelta
from django.utils import timezone

logger = logging.getLogger(__name__)

class EmployeeService:
    def __init__(self, bitrix_token):
        self.but = bitrix_token

    def get_employees_data(self):
        methods = [
            (
                "users",
                "user.get",
                {
                    "filter": {"ACTIVE": True},
                    "select": [
                        "ID",
                        "NAME",
                        "LAST_NAME",
                        "SECOND_NAME",
                        "UF_DEPARTMENT",
                    ],
                },
            ),
            ("departments", "department.get", {}),
        ]

        batch_result = self.but.batch_api_call(methods=methods)

        users = batch_result.get("users", {}).get("result", [])
        departments = batch_result.get("departments", {}).get("result", [])

        department_heads = self._get_department_heads(departments)
        users_by_id = {int(user["ID"]): user for user in users}
        departments_by_id = {str(dept["ID"]): dept["NAME"] for dept in departments}

        user_calls = self._get_calls_statistics(users)

        employees_data = []
        for user in users:
            full_name = f"{user.get('LAST_NAME', '')} {user.get('NAME', '')} {user.get('SECOND_NAME', '')}".strip()

            managers = self._build_manager_chain(user, users_by_id, department_heads)
            managers_names = [
                f"{m.get('LAST_NAME', '')} {m.get('NAME', '')}".strip()
                for m in managers
            ]

            department_ids = user.get("UF_DEPARTMENT", [])
            department_name = ""
            if department_ids:
                department_name = departments_by_id.get(
                    str(department_ids[0]), "Не указан"
                )

            employees_data.append(
                {
                    "id": user.get("ID"),
                    "name": full_name,
                    "department": department_name,
                    "managers": managers_names,
                    "calls_count": user_calls.get(str(user.get("ID")), 0),
                }
            )
        
        return employees_data

    def _get_department_heads(self, departments):
        department_heads = {}
        for dept in departments:
            dept_id = dept.get("ID")
            head_id = dept.get("UF_HEAD")
            if dept_id and head_id:
                department_heads[int(dept_id)] = int(head_id)
        return department_heads

    def _build_manager_chain(self, user, users_by_id, department_heads):
        managers = []
        user_departments = user.get("UF_DEPARTMENT", [])

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
            if manager and manager.get("ID") != user.get("ID"):
                managers.append(manager)

                manager_depts = manager.get("UF_DEPARTMENT", [])
                current_dept = int(manager_depts[0]) if manager_depts else None
            else:
                break

        return managers

    def _get_calls_statistics(self, users):
        user_calls = {str(user["ID"]): 0 for user in users}

        try:
            now = timezone.now()
            date_from = now - timedelta(hours=24)

            all_calls = self.but.call_list_fast(
                "voximplant.statistic.get",
                params={
                    "filter": {
                        "START_DATE": date_from.isoformat(),
                        "END_DATE": now.isoformat(),
                        "TYPE": "out",
                    },
                    "select": ["PORTAL_USER_ID", "CALL_DURATION"],
                },
            )

            logger.info("Fetching all calls from the last 24 hours...")

            count = 0
            for call in all_calls:
                count += 1
                duration = int(call.get("CALL_DURATION", 0))
                user_id = str(call.get("PORTAL_USER_ID", ""))

                if duration > 60:
                    if user_id in user_calls:
                        user_calls[user_id] += 1
                        logger.info(
                            f"Counted call for user {user_id} with duration {duration}s"
                        )
                    else:
                        logger.warning(
                            f"User {user_id} from call stats not in the initial user list."
                        )

            logger.info(f"Processed {count} total calls from voximplant.statistic.get")
            logger.info(f"Получена статистика звонков для {len(user_calls)} пользователей")
            return user_calls

        except Exception as e:
            logger.error(f"Ошибка при получении статистики звонков: {e}")
            return user_calls
