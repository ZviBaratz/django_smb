from django import forms
from django_smb.models import RemoteLocation


class RemoteLocationForm(forms.ModelForm):
    class Meta:
        model = RemoteLocation
        fields = [
            'name',
            'server_name',
            'share_name',
            'user_id',
            'password',
        ]
        widgets = {
            'password': forms.PasswordInput(),
        }