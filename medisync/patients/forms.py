from django import forms
from .models import PatientDocument
from django.core.exceptions import ValidationError
import os  # Pour l'analyse des extensions de fichier

class PatientDocumentForm(forms.ModelForm):
    class Meta:
        model = PatientDocument
        fields = ['document', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_document(self):
        document = self.cleaned_data.get('document')
        if document:
            # Extensions autorisées (en minuscules)
            allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf', '.docx']
            ext = os.path.splitext(document.name)[1].lower()  # Récupère l'extension
            
            # Vérification de l'extension
            if ext not in allowed_extensions:
                raise ValidationError(
                    "Format de fichier non autorisé. Seuls les fichiers JPG, PNG, PDF et DOCX sont acceptés."
                )
            
            # Validation supplémentaire du type MIME (optionnel mais recommandé)
            try:
                mime_type = document.content_type
                allowed_mime_types = [
                    'image/jpeg',
                    'image/png',
                    'application/pdf',
                    'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                ]
                if mime_type not in allowed_mime_types:
                    raise ValidationError("Type de fichier non supporté.")
            except AttributeError:
                pass  # Si content_type n'est pas disponible
            
        return document