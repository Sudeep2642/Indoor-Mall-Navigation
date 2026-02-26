"""QR code generator — one QR per Location."""
import qrcode
from io import BytesIO
from django.core.files.base import ContentFile


def make_qr(url: str) -> BytesIO:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf


def generate_for_location(location, base_url: str):
    """Generate and save QR to location.qr_image field."""
    url = location.qr_url_data(base_url)
    buf = make_qr(url)
    filename = f"qr_{location.mall.slug}_{location.code}.png"
    location.qr_image.save(filename, ContentFile(buf.read()), save=True)
    return url
