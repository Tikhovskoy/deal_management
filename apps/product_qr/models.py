import uuid

from django.db import models


class ProductQR(models.Model):
    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_id = models.CharField(max_length=50)
    member_id = models.CharField(max_length=50, blank=True, null=True)
    product_data = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "QR-код товара"
        verbose_name_plural = "QR-коды товаров"

    def __str__(self):
        return f"QR for product {self.product_id}"
