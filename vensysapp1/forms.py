
#Create forms to handle file uploads.

from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

