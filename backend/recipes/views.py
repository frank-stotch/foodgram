from django.shortcuts import redirect


def short_link_view(request, pk):
    return redirect("api:recipes-detail", kwargs={"pk": pk})
