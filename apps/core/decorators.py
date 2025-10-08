from functools import wraps
from django.views.decorators.csrf import csrf_exempt
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth

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
