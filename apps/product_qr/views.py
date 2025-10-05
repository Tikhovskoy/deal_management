from django.shortcuts import render, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from integration_utils.bitrix24.bitrix_user_auth.main_auth import main_auth
from functools import wraps
from .models import ProductQR
import qrcode
from io import BytesIO
import base64
from django.conf import settings
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


@smart_auth
def index(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id', '').strip()

        if product_id:
            try:
                product_response = request.bitrix_user_token.call_api_method(
                    'crm.product.get',
                    {'id': product_id}
                )

                if 'result' in product_response:
                    product = product_response['result']

                    qr_record = ProductQR.objects.create(
                        product_id=product_id,
                        member_id=request.bitrix_user_token.member_id
                    )

                    public_url = f"{settings.APP_SETTINGS.app_domain}/qr/view/{qr_record.uuid}/"

                    qr = qrcode.QRCode(
                        version=1,
                        error_correction=qrcode.constants.ERROR_CORRECT_L,
                        box_size=10,
                        border=4,
                    )
                    qr.add_data(public_url)
                    qr.make(fit=True)

                    img = qr.make_image(fill_color="black", back_color="white")

                    buffer = BytesIO()
                    img.save(buffer, format='PNG')
                    img_str = base64.b64encode(buffer.getvalue()).decode()

                    context = {
                        'product': product,
                        'qr_image': img_str,
                        'public_url': public_url,
                        'uuid': str(qr_record.uuid)
                    }
                    return render(request, 'product_qr/generated.html', context)
                else:
                    error = 'Товар не найден'
            except Exception as e:
                logger.error(f"Error generating QR: {str(e)}")
                error = f'Ошибка: {str(e)}'

            return render(request, 'product_qr/index.html', {'error': error})

    return render(request, 'product_qr/index.html')


def view_product(request, uuid):
    qr_record = get_object_or_404(ProductQR, uuid=uuid)

    try:
        product_response = request.bitrix_user_token.call_api_method(
            'crm.product.get',
            {'id': qr_record.product_id}
        )

        if 'result' in product_response:
            product = product_response['result']

            context = {
                'product': product,
                'qr_uuid': str(qr_record.uuid)
            }
            return render(request, 'product_qr/view.html', context)
        else:
            return HttpResponse('Товар не найден', status=404)
    except Exception as e:
        logger.error(f"Error viewing product: {str(e)}")
        return HttpResponse('Ошибка получения данных товара', status=500)
