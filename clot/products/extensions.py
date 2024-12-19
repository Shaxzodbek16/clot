from slugify import slugify


def generate_unique_slug(instance, value, slug_field_name="slug"):
    base_slug = slugify(value)
    slug = base_slug
    counter = 1
    while instance.__class__.objects.filter(**{slug_field_name: slug}).exists():
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug
