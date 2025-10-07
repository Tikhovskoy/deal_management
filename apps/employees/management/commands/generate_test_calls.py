from django.core.management.base import BaseCommand
from datetime import timedelta
from django.utils import timezone
import random
import os
import time


class Command(BaseCommand):
    help = "Генерирует тестовые звонки для указанных пользователей"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count", type=int, default=10, help="Количество звонков для генерации"
        )
        parser.add_argument(
            "--user-ids",
            type=str,
            help="ID пользователей через запятую (например: 1,2,3)",
        )

    def handle(self, *args, **options):
        count = options["count"]
        user_ids_str = options.get("user_ids")

        if not user_ids_str:
            self.stdout.write(self.style.ERROR("Необходимо указать --user-ids"))
            return

        user_ids = [uid.strip() for uid in user_ids_str.split(",")]

        webhook_url = os.getenv("BITRIX_WEBHOOK_URL")
        if not webhook_url:
            self.stdout.write(self.style.ERROR("BITRIX_WEBHOOK_URL не настроен в .env"))
            return

        import requests

        self.stdout.write(
            f"Генерация {count} тестовых звонков для пользователей: {', '.join(user_ids)}"
        )

        now = timezone.now()
        successful = 0
        failed = 0

        for i in range(count):
            user_id = random.choice(user_ids)

            call_start = now - timedelta(
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
                seconds=random.randint(0, 59),
            )

            duration = random.randint(61, 300)

            phone_number = f"+7{random.randint(9000000000, 9999999999)}"

            call_id = f"test_call_{user_id}_{int(call_start.timestamp())}"

            params = {
                "USER_ID": user_id,
                "PHONE_NUMBER": phone_number,
                "TYPE": "1",
                "CRM_CREATE": "1",
                "SHOW": "0",
            }

            try:
                response = requests.post(
                    f"{webhook_url}telephony.externalcall.register",
                    json=params,
                    timeout=10,
                )

                if response.status_code == 200:
                    data = response.json()
                    if "result" in data:
                        returned_call_id = data["result"].get("CALL_ID", call_id)
                        self.stdout.write(
                            f"  Зарегистрирован звонок с CALL_ID: {returned_call_id}"
                        )

                        time.sleep(2)

                        finish_params = {
                            "CALL_ID": returned_call_id,
                            "USER_ID": user_id,
                            "DURATION": duration,
                            "STATUS_CODE": "200",
                            "ADD_TO_CHAT": 0,
                        }

                        finish_response = requests.post(
                            f"{webhook_url}telephony.externalcall.finish",
                            json=finish_params,
                            timeout=10,
                        )

                        if finish_response.status_code == 200:
                            finish_data = finish_response.json()
                            if "result" in finish_data:
                                crm_activity_id = finish_data["result"].get(
                                    "CRM_ACTIVITY_ID"
                                )

                                if crm_activity_id:
                                    update_response = requests.post(
                                        f"{webhook_url}crm.activity.update",
                                        json={
                                            "id": crm_activity_id,
                                            "fields": {
                                                "DESCRIPTION": f"Длительность: {duration} сек"
                                            },
                                        },
                                        timeout=10,
                                    )

                                    if update_response.status_code == 200:
                                        self.stdout.write(
                                            f"  Обновлена активность {crm_activity_id} с длительностью {duration}с"
                                        )

                                successful += 1
                                self.stdout.write(
                                    f"[{i + 1}/{count}] Создан и завершен звонок для пользователя {user_id}, "
                                    f"длительность: {duration}с"
                                )
                            else:
                                failed += 1
                                self.stdout.write(
                                    self.style.WARNING(
                                        f"[{i + 1}/{count}] Ошибка finish API: {finish_data.get('error_description', 'Unknown')}"
                                    )
                                )
                        else:
                            failed += 1
                            finish_error = (
                                finish_response.json()
                                if finish_response.content
                                else {}
                            )
                            self.stdout.write(
                                self.style.WARNING(
                                    f"[{i + 1}/{count}] Ошибка finish ({finish_response.status_code}): "
                                    f"{finish_error.get('error_description', 'Unknown')}"
                                )
                            )
                    else:
                        failed += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f"[{i + 1}/{count}] Ошибка API: {data.get('error_description', 'Unknown')}"
                            )
                        )
                else:
                    failed += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"[{i + 1}/{count}] HTTP ошибка: {response.status_code}"
                        )
                    )

            except Exception as e:
                failed += 1
                self.stdout.write(
                    self.style.ERROR(f"[{i + 1}/{count}] Исключение: {str(e)}")
                )

        self.stdout.write(
            self.style.SUCCESS(f"\nГотово! Успешно: {successful}, Ошибок: {failed}")
        )
