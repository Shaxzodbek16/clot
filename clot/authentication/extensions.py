from multiprocessing.connection import Client

from slugify import slugify
import random


def generate_unique_slug(instance, value, slug_field_name="slug"):
    base_slug = slugify(value)
    slug = base_slug
    counter = 1
    while instance.__class__.objects.filter(**{slug_field_name: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def generate_code():
    return random.randint(100000, 999999)


def send_sms(phone_number, name, code, template="verification"):
    pass
