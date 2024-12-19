# myapp/utils.py
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import Rating

def get_average_rating(obj):
    
    content_type = ContentType.objects.get_for_model(obj)
    
    
    avg = Rating.objects.filter(
        content_type=content_type,
        object_id=obj.id
    ).aggregate(Avg('score'))['score__avg']

    if avg is None:
        avg = 0.0
    return round(avg, 1)
