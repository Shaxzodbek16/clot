from pyexpat.errors import messages

from slugify import slugify
import random

from .views import SMSMessage


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


def send_sms(phone_number, name, code, type=SMSMessage.REGISTRATION.value):
    import http.client
    import json
    message = ""
    if type == 'registration':
        message = f"Hello, {name}. Your code is {code} to complete your registration"
    elif type == 'forgot_password':
        message = f"Hello, {name}. Your code is {code} to reset your password"

    conn = http.client.HTTPSConnection("e144zn.api.infobip.com")
    payload = json.dumps({
        "messages": [
            {
                "destinations": [{"to": f"{phone_number}".replace("+", "")}],
                "from": "447491163443",
                "text": message
            }
        ]
    })
    headers = {
        'Authorization': 'App b3e7007650143d8e54f017036763bc62-c0e39705-f634-4448-acbb-19d8626fe829',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    conn.request("POST", "/sms/2/text/advanced", payload, headers)
    res = conn.getresponse()
    data = res.read()
    print(data.decode("utf-8"))


if __name__ == "__main__":
    phone_number = "+998915260112"
    name = "Shaxzodbek"
    code = generate_code()
    send_sms(phone_number, name, code)
    print(code)
