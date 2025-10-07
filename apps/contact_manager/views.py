import csv
import io
from functools import wraps

import openpyxl
from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from openpyxl.styles.fills import PatternFill

from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

original_init = PatternFill.__init__


def new_init(self, *args, **kwargs):
    kwargs.pop("extLst", None)
    original_init(self, *args, **kwargs)


PatternFill.__init__ = new_init


def smart_auth(func):
    @csrf_exempt
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        has_auth_id = request.POST.get("AUTH_ID") or request.GET.get("AUTH_ID")

        if has_auth_id:
            return main_auth(on_start=True, set_cookie=True)(func)(
                request, *args, **kwargs
            )
        else:
            return main_auth(on_cookies=True, set_cookie=True)(func)(
                request, *args, **kwargs
            )

    return wrapper


@smart_auth
def index(request):
    return render(request, "contact_manager/index.html")


@smart_auth
def export_contacts(request):
    if request.method == "POST":
        try:
            but = request.bitrix_user_token
            file_format = request.POST.get("format", "csv")

            contacts = but.call_list_fast(
                "crm.contact.list",
                {"select": ["ID", "NAME", "LAST_NAME", "COMPANY_ID", "PHONE", "EMAIL"]},
            )
            contacts = list(contacts)

            companies_data = but.call_list_fast(
                "crm.company.list", {"select": ["ID", "TITLE"]}
            )
            company_map = {str(c["ID"]): c["TITLE"] for c in companies_data}

            header = ["имя", "фамилия", "номер телефона", "почта", "компания"]

            if file_format == "xlsx":
                workbook = openpyxl.Workbook()
                sheet = workbook.active
                sheet.title = "Contacts"
                sheet.append(header)

                for contact in contacts:
                    phone = (
                        contact.get("PHONE")[0]["VALUE"] if contact.get("PHONE") else ""
                    )
                    email = (
                        contact.get("EMAIL")[0]["VALUE"] if contact.get("EMAIL") else ""
                    )
                    company_name = company_map.get(str(contact.get("COMPANY_ID")), "")
                    sheet.append(
                        [
                            contact.get("NAME", ""),
                            contact.get("LAST_NAME", ""),
                            phone,
                            email,
                            company_name,
                        ]
                    )

                buffer = io.BytesIO()
                workbook.save(buffer)
                buffer.seek(0)

                response = HttpResponse(
                    buffer.getvalue(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
                response["Content-Disposition"] = 'attachment; filename="contacts.xlsx"'
                return response

            else:
                response = HttpResponse(content_type="text/csv; charset=utf-8")
                response["Content-Disposition"] = 'attachment; filename="contacts.csv"'
                response.write("\ufeff".encode("utf8"))

                writer = csv.writer(response)
                writer.writerow(header)

                for contact in contacts:
                    phone = (
                        contact.get("PHONE")[0]["VALUE"] if contact.get("PHONE") else ""
                    )
                    email = (
                        contact.get("EMAIL")[0]["VALUE"] if contact.get("EMAIL") else ""
                    )
                    company_name = company_map.get(str(contact.get("COMPANY_ID")), "")

                    writer.writerow(
                        [
                            contact.get("NAME", ""),
                            contact.get("LAST_NAME", ""),
                            phone,
                            email,
                            company_name,
                        ]
                    )

                return response

        except Exception as e:
            return render(request, "contact_manager/export.html", {"error": str(e)})

    return render(request, "contact_manager/export.html")


@smart_auth
def import_contacts(request):
    context = {}
    if request.method == "POST":
        if not request.FILES.get("file"):
            context["error"] = "Файл не был загружен."
            return render(request, "contact_manager/import.html", context)

        file = request.FILES["file"]

        original_rows = []
        try:
            if file.name.endswith(".csv"):
                decoded_file = file.read().decode("utf-8-sig")
                lines = decoded_file.strip().splitlines()
                header = [h.lower().strip() for h in lines[0].split(",")]
                for line in lines[1:]:
                    values = line.split(",")
                    original_rows.append(dict(zip(header, values)))
            elif file.name.endswith(".xlsx"):
                workbook = openpyxl.load_workbook(file)
                sheet = workbook.active
                header = [cell.value.lower().strip() for cell in sheet[1]]
                for row in sheet.iter_rows(min_row=2, values_only=True):
                    original_rows.append(dict(zip(header, row)))
            else:
                context["error"] = (
                    "Неподдерживаемый формат файла. Пожалуйста, используйте CSV или XLSX."
                )
                return render(request, "contact_manager/import.html", context)

            required_headers = ["имя", "фамилия"]
            if not all(h in header for h in required_headers):
                error_msg = (
                    f"Ошибка в заголовках файла. Убедитесь, что файл содержит обязательные колонки: {required_headers}. "
                    f"Найденные заголовки: {header}."
                )
                context["error"] = error_msg
                return render(request, "contact_manager/import.html", context)

            but = request.bitrix_user_token

            existing_contacts = but.call_list_fast(
                "crm.contact.list", {"select": ["PHONE", "EMAIL"]}
            )
            existing_phones = set()
            existing_emails = set()
            for contact in existing_contacts:
                if contact.get("PHONE"):
                    existing_phones.add(contact["PHONE"][0]["VALUE"])
                if contact.get("EMAIL"):
                    existing_emails.add(contact["EMAIL"][0]["VALUE"])

            companies_data = but.call_list_fast(
                "crm.company.list", {"select": ["ID", "TITLE"]}
            )
            company_map = {
                c["TITLE"].lower().strip(): str(c["ID"]) for c in companies_data
            }

            batch_cmds = []
            skipped_details = []
            for i, row in enumerate(original_rows):
                name = row.get("имя")
                last_name = row.get("фамилия")
                phone = row.get("номер телефона")
                email = row.get("почта")
                company_name = row.get("компания")

                if not name and not last_name:
                    continue

                contact_name_for_report = f"{name or ''} {last_name or ''}".strip()

                if phone and phone in existing_phones:
                    skipped_details.append(
                        f"Строка {i + 2}: Контакт '{contact_name_for_report}' пропущен (дубликат по номеру телефона: {phone})."
                    )
                    continue
                if email and email in existing_emails:
                    skipped_details.append(
                        f"Строка {i + 2}: Контакт '{contact_name_for_report}' пропущен (дубликат по email: {email})."
                    )
                    continue

                fields = {
                    "NAME": name,
                    "LAST_NAME": last_name,
                    "OPENED": "Y",
                    "ASSIGNED_BY_ID": request.bitrix_user_token.user.bitrix_id,
                }
                if phone:
                    fields["PHONE"] = [{"VALUE": phone, "VALUE_TYPE": "WORK"}]
                if email:
                    fields["EMAIL"] = [{"VALUE": email, "VALUE_TYPE": "WORK"}]

                if company_name:
                    company_id = company_map.get(str(company_name).lower().strip())
                    if company_id:
                        fields["COMPANY_ID"] = company_id

                batch_cmds.append((f"cmd_{i}", "crm.contact.add", {"fields": fields}))

            context["skipped_count"] = len(skipped_details)
            context["skipped_details"] = skipped_details

            if batch_cmds:
                result = but.batch_api_call(batch_cmds)
                success_details = []
                error_details = []

                if result:
                    for cmd_id, res in result.items():
                        index = int(cmd_id.split("_")[1])
                        row_num = index + 2
                        original_row_data = original_rows[index]
                        contact_name = f"{original_row_data.get('имя', '')} {original_row_data.get('фамилия', '')}".strip()

                        if res.get("error") is None:
                            success_details.append(
                                f"Строка {row_num}: Контакт '{contact_name}' успешно создан (ID: {res.get('result')})."
                            )
                        else:
                            error_msg = res["error"].get(
                                "error_description", "Неизвестная ошибка"
                            )
                            error_details.append(
                                f"Строка {row_num}: Ошибка при создании контакта '{contact_name}' - {error_msg}"
                            )

                context["success_count"] = len(success_details)
                context["error_count"] = len(error_details)
                context["success_details"] = success_details
                context["error_details"] = error_details

        except Exception as e:
            context["error"] = f"Произошла ошибка при обработке файла: {str(e)}"

    return render(request, "contact_manager/import.html", context)
