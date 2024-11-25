from django import forms
from .models import FlashCardSet, FlashCard

class FlashCardSetForm(forms.ModelForm):
    class Meta:
        model = FlashCardSet
        fields = ['name']

class FlashCardForm(forms.ModelForm):
    class Meta:
        model = FlashCard
        fields = ['question', 'answer', 'difficulty']
