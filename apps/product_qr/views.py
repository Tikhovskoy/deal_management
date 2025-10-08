import logging
import os

import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.core.decorators import smart_auth

from .models import ProductQR
from .services import ProductQRService

logger = logging.getLogger(__name__)


def extract_product_image_url(product):
    if product.get("PREVIEW_PICTURE"):
        return product.get("PREVIEW_PICTURE")

    if product.get("DETAIL_PICTURE"):
        return product.get("DETAIL_PICTURE")

    for key, value in product.items():
        if key.startswith("PROPERTY_") and isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict) and "value" in value[0]:
                file_data = value[0]["value"]
                if isinstance(file_data, dict) and "downloadUrl" in file_data:
                    domain = settings.APP_SETTINGS.portal_domain
                    return f"https://{domain}{file_data['downloadUrl']}"

    return None


def call_bitrix_webhook(method, params=None):
    webhook_url = os.getenv("BITRIX_WEBHOOK_URL")
    if not webhook_url:
        raise ValueError("BITRIX_WEBHOOK_URL not configured")

    url = f"{webhook_url}{method}"
    response = requests.post(url, json=params or {}, timeout=10)
    response.raise_for_status()

    data = response.json()
    if "error" in data:
        raise ValueError(data.get("error_description", "Bitrix API error"))

    return data


@smart_auth
def index(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id", "").strip()

        if product_id:
            try:
                service = ProductQRService(request.bitrix_user_token)
                context = service.generate_qr_code(product_id)
                return render(request, "product_qr/generated.html", context)
            except Exception as e:
                logger.error("Error generating QR: %s", str(e))
                error = str(e)
                return render(request, "product_qr/index.html", {"error": error})

    return render(request, "product_qr/index.html")


def view_product(request, uuid):
    qr_record = get_object_or_404(ProductQR, uuid=uuid)

    try:
        product = qr_record.product_data if qr_record.product_data else {}

        if not product:
            product_response = call_bitrix_webhook(
                "crm.product.get", {"id": qr_record.product_id}
            )
            if "result" in product_response:
                product = product_response["result"]

        image_url = extract_product_image_url(product)

        context = {
            "product": product,
            "image_url": image_url,
            "qr_uuid": str(qr_record.uuid),
        }
        return render(request, "product_qr/view.html", context)
    except Exception as e:
        logger.error("Error viewing product: %s", str(e))
        return HttpResponse("Ошибка получения данных товара", status=500)
