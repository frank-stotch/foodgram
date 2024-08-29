from http import HTTPStatus

from rest_framework.decorators import action
from djoser.views import UserViewSet as DjoserUserViewSet
from rest_framework import viewsets
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from . import serializers
from recipes.models import Tag


class UserViewSet(DjoserUserViewSet):
    def get_permissions(self):
        if self.action == "me":
            return (IsAuthenticated(),)
        if self.action == "retrieve":
            return (AllowAny(),)
        return super().get_permissions()

    @action(
        detail=False,
        methods=("put", "delete"),
        permission_classes=(IsAuthenticated,),
        url_path="me/avatar"
    )
    def avatar(self, request):
        user = request.user
        if request.method == "PUT":
            serializer = serializers.AvatarSerializer(data=request.data)
            if serializer.is_valid():
                user.avatar = serializer.validated_data["avatar"]
                user.save()
                return Response(
                    serializers.AvatarSerializer(user).data, status=HTTPStatus.OK
                )
            return Response(serializer.errors, status=HTTPStatus.BAD_REQUEST)
        user.avatar.delete(save=True)
        return Response(status=HTTPStatus.NO_CONTENT)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = serializers.TagSerializer
    pagination_class = None
    permission_classes = (AllowAny,)
