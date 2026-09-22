import os
from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.prod")
django_asgi_app = get_asgi_application()

from channels.routing import ProtocolTypeRouter

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    # "websocket": ... real-time avatar audio stream uchun keyinchalik qo'shiladi
})    