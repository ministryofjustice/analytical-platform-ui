from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import ListView

from .models import SharedResource
from .utils import create_or_update_shared_resources


class SharedResourceListView(ListView):
    template_name = "poc/shared_resources.html"
    model = SharedResource
    context_object_name = "ram_shares"


# class RAMShareResourcesView(DetailView):
#     template_name = "poc/ram_share_resources.html"
#     model = RAMShare
#     context_object_name = "ram_share"

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context["resources"] = list(self.object.get_shared_resources())
#         return context


class RefreshSharedResourceView(View):
    def post(self, request, *args, **kwargs):
        try:
            create_or_update_shared_resources()
            messages.success(request, "Shared Resources have been successfully refreshed.")
        except Exception as e:
            messages.error(request, f"Failed to refresh Shared Resources: {str(e)}")

        return HttpResponseRedirect(reverse("poc:index"))


class DeleteSharedResourceView(View):
    def post(self, request, *args, **kwargs):
        for obj in SharedResource.objects.all():
            obj.delete()
        messages.success(request, "Shared Resources have been successfully deleted.")
        return HttpResponseRedirect(reverse("poc:index"))
