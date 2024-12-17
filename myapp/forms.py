from django import forms
from .models import FlashCardSet, FlashCard, Collection, Comment, Tag
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class FlashCardSetForm(forms.ModelForm):
    
    tag_names = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = FlashCardSet
        fields = ['name']  
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border rounded',
                'placeholder': 'Set Name'
            }),
        }
        labels = {
            'name': 'Set Name',
        }

    def clean(self):
        cleaned_data = super().clean()
        
        return cleaned_data


class FlashCardForm(forms.ModelForm):
    class Meta:
        model = FlashCard
        fields = ['question', 'answer', 'difficulty']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded',
                'placeholder': 'Question',
                'rows': 4,
            }),
            'answer': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded',
                'placeholder': 'Answer',
                'rows': 4,
            }),
            'difficulty': forms.Select(attrs={
                'class': 'w-full px-3 py-2 border rounded',
            }),
        }


class CustomUserCreationForm(UserCreationForm):
    username = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'Username'
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'Password'
        })
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'w-full px-3 py-2 border rounded',
            'placeholder': 'Confirm Password'
        })
    )

    class Meta:
        model = User
        fields = ['username', 'password1', 'password2']


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'border border-gray-300 rounded px-3 py-2 w-full'}),
            'description': forms.Textarea(attrs={'class': 'border border-gray-300 rounded px-3 py-2 w-full'}),
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border rounded',
                'placeholder': 'Add a comment...',
                'rows': 3,
            }),
        }
