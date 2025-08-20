from django import forms
from .models import Agreement

class AgreementForm(forms.ModelForm):
    class Meta:
        model = Agreement
        fields = ["pdf"]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pdf'].widget.attrs.update({
            'accept': '.pdf',
            'class': 'form-control-file'
        })
