from django.contrib import admin

# Register your models here.

from .models import WebhookMessage, Player, Competition



admin.site.register(WebhookMessage)
admin.site.register(Player)
admin.site.register(Competition)
