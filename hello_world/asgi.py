"""
ASGI config for hello_world project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.0/howto/deployment/asgi/
"""



#This is the configuration to run your project as an ASGI application with ASGI-compatible web servers. 
# ASGI is the emerging Python standard for asynchronous web servers and applications.



import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hello_world.settings")

application = get_asgi_application()
