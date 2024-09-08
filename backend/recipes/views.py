from django.shortcuts import redirect
from django.urls import reverse


def short_link_view(request, pk):
    return redirect(reverse("api:recipes-detail", kwargs={"pk": pk}))
