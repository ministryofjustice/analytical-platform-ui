from django import forms

from ap.users.models import User

from . import models


class AccessForm(forms.ModelForm):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    access_levels = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.table_name = kwargs.pop("table_name")
        self.database_name = kwargs.pop("database_name")
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["access_levels"].queryset = self.grantable_access

    class Meta:
        model = models.TableAccess
        fields = ["access_levels"]

    def clean(self):
        cleaned_data = super().clean()
        try:
            self._meta.model.objects.get(
                name=self.table_name, database_access__user=cleaned_data["user"]
            )
            raise forms.ValidationError("Selected user already has access to this table.")
        except self._meta.model.DoesNotExist:
            pass

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = self.table_name
        instance.database_access = models.DatabaseAccess.objects.get_or_create(
            user=self.cleaned_data["user"], name=self.database_name
        )[0]
        instance.save()
        self.save_m2m()
        return instance


class ManageAccessForm(forms.ModelForm):
    access_levels = forms.ModelMultipleChoiceField(queryset=None)

    def __init__(self, *args, **kwargs):
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["access_levels"].queryset = self.grantable_access

    class Meta:
        model = models.TableAccess
        fields = ["access_levels"]