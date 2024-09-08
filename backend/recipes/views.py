from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from .models import Recipe


def short_link_view(request, pk):
    get_object_or_404(Recipe, pk=pk)
    return redirect(reverse("api:recipes-detail", kwargs={"pk": pk}))
