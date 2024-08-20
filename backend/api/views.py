from rest_framework.viewsets import ReadOnlyModelViewSet

from recipes.models import Tag
from .serializers import TagSerializer


class TagViewSet(ReadOnlyModelViewSet):
    http_method_names = ["get"]
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
