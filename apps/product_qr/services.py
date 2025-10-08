import base64
from io import BytesIO

import qrcode
from django.conf import settings

from .models import ProductQR

QR_VERSION = 1
QR_BOX_SIZE = 10
QR_BORDER = 4
QR_IMAGE_FORMAT = "PNG"


class ProductQRService:
    def __init__(self, bitrix_user_token):
        self.but = bitrix_user_token

    def generate_qr_code(self, product_id):
        if not product_id.isdigit():
            raise ValueError("ID товара должен быть числом")

        product_response = self.but.call_api_method("crm.product.get", {"id": product_id})

        if "error" in product_response:
            raise ValueError(f"Товар с ID {product_id} не найден. Проверьте правильность ID товара.")

        if "result" not in product_response:
            raise ValueError("Некорректный ответ от API. Попробуйте еще раз.")

        product = product_response["result"]

        member_id = getattr(self.but, "member_id", None)
        qr_record = ProductQR.objects.create(
            product_id=product_id, member_id=member_id, product_data=product
        )

        public_url = f"https://{settings.APP_SETTINGS.app_domain}/qr/view/{qr_record.uuid}/"

        qr = qrcode.QRCode(
            version=QR_VERSION,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=QR_BOX_SIZE,
            border=QR_BORDER,
        )
        qr.add_data(public_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        buffer = BytesIO()
        img.save(buffer, format=QR_IMAGE_FORMAT)
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return {
            "product": product,
            "qr_image": img_str,
            "public_url": public_url,
            "uuid": str(qr_record.uuid),
        }
