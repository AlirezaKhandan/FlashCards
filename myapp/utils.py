# myapp/utils.py
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from .models import Rating

def get_average_rating(obj):
    """
    Given any model instance `obj` that can be rated, 
    returns the average rating as a float rounded to one decimal place.
    If there are no ratings, returns 0.0.
    """
    # Get the content type for this object's model
    content_type = ContentType.objects.get_for_model(obj)
    
    # Calculate the average rating for this specific object
    avg = Rating.objects.filter(
        content_type=content_type,
        object_id=obj.id
    ).aggregate(Avg('score'))['score__avg']

    if avg is None:
        avg = 0.0
    return round(avg, 1)
