import sys
from django.apps import AppConfig

class AppointmentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appointments'

    def ready(self):
        if 'runserver' in sys.argv:
            import threading
            from .scheduler import start
        
            def delayed_start():
                import time
                time.sleep(10)  # Délai de 10 secondes
                start()
        
            threading.Thread(target=delayed_start).start()
