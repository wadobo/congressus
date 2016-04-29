import barcode
import os
from barcode.writer import ImageWriter
from django.conf import settings


def generate_barcode(order, path='barcodes'):
    """
    Generate barcode with order param. This order param should be a
    alphanumeric character.
    """
    provided = barcode.get_barcode_class('code39')
    codigo = provided(order, writer=ImageWriter())
    fullname = codigo.save(os.path.join(settings.MEDIA_ROOT, path, order))
    return fullname
