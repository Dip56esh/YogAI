from django.apps import AppConfig


class YogaBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'yoga_backend'
    
    def ready(self):
        """Initialize the pose detector when Django starts"""
        pass