from django.apps import AppConfig

class AdministratorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'administrators'

    def ready(self):
        import administrators.signals

# accounts/apps.py
def ready(self):
    import accounts.signals


from django.apps import AppConfig

class DoctorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'doctors'
    
    def ready(self):
        import doctors.signals