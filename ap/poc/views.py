from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView, ListView

from .models import RAMShare
from .utils import create_or_update_ram_objects


class RAMShareView(ListView):
    template_name = "poc/ram_share.html"
    model = RAMShare
    context_object_name = "ram_shares"


class RAMShareResourcesView(DetailView):
    template_name = "poc/ram_share_resources.html"
    model = RAMShare
    context_object_name = "ram_share"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["resources"] = self.object.get_shared_resources()
        return context


class RefreshRAMSharesView(View):
    def post(self, request, *args, **kwargs):
        try:
            create_or_update_ram_objects()
            messages.success(request, "RAM shares have been successfully refreshed.")
        except Exception as e:
            messages.error(request, f"Failed to refresh RAM shares: {str(e)}")

        return HttpResponseRedirect(reverse("poc:index"))


class DeleteRAMSharesView(View):
    def post(self, request, *args, **kwargs):
        for obj in RAMShare.objects.all():
            obj.delete()
        messages.success(request, "RAM shares have been successfully deleted.")
        return HttpResponseRedirect(reverse("poc:index"))
