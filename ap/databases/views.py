from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from .forms import ProjectForm
from .models import Project


class ProjectListView(ListView):
    model = Project


class ProjectDetailView(DetailView):
    model = Project


class ProjectCreateView(CreateView):
    form_class = ProjectForm
    template_name = "databases/project_create.html"
    success_url = reverse_lazy("databases:index")
