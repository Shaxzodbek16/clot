from django.contrib import admin
from .models import User, Address, Notification

admin.site.register(User)
admin.site.register(Address)
admin.site.register(Notification)
