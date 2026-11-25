from django import forms
from django.contrib.auth.models import User
from .models import Document, Category, Tag, DocumentComment
class DocumentForm(forms.ModelForm):
    tags_text=forms.CharField(required=False,help_text="Comma-separated tags")
    class Meta:
        model=Document
        fields=["title","description","file","category","status"]
        widgets={"description":forms.Textarea(attrs={"rows":3})}
    def save(self,commit=True):
        obj=super().save(commit=commit)
        if commit:
            names=[x.strip() for x in self.cleaned_data.get("tags_text","").split(",") if x.strip()]
            obj.tags.set([Tag.objects.get_or_create(name=n)[0] for n in names])
        return obj
class VersionForm(forms.Form):
    file=forms.FileField()
    change_note=forms.CharField(required=False,widget=forms.Textarea(attrs={"rows":2}))
class PermissionForm(forms.Form):
    username=forms.CharField()
    permission_type=forms.ChoiceField(choices=[("view","View"),("edit","Edit"),("delete","Delete"),("download","Download"),("share","Share")])
class ShareForm(forms.Form):
    username=forms.CharField()
    expires_at=forms.DateTimeField(required=False,widget=forms.DateTimeInput(attrs={"type":"datetime-local"}))
class CommentForm(forms.ModelForm):
    class Meta:
        model=DocumentComment
        fields=["comment"]
        widgets={"comment":forms.Textarea(attrs={"rows":2,"placeholder":"Write a comment..."})}
