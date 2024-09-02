from django import forms

from ap.users.models import User

from . import models


class AccessForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Select a user to grant access to",
        template_name="forms/fields/select.html",
    )
    access_levels = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        template_name="forms/fields/checkbox.html",
        help_text="Select all that apply",
    )

    def __init__(self, *args, **kwargs):
        self.table_name = kwargs.pop("table_name")
        self.database_name = kwargs.pop("database_name")
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["access_levels"].queryset = self.grantable_access

    class Meta:
        model = models.TableAccess
        fields = ["access_levels"]

    def clean_user(self):
        user = self.cleaned_data.get("user")
        try:
            self._meta.model.objects.get(name=self.table_name, database_access__user=user)
            raise forms.ValidationError("Selected user already has access to this table.")
        except self._meta.model.DoesNotExist:
            pass

        return user

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("access_levels"):
            raise forms.ValidationError("You must select at least one access level.")
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.name = self.table_name
        database_access, created = models.DatabaseAccess.objects.get_or_create(
            user=self.cleaned_data["user"], name=self.database_name
        )
        instance.database_access = database_access
        instance.save()
        self.save_m2m()
        instance.grant_lakeformation_permissions(create_hybrid_opt_in=True)
        if created:
            database_access.grant_lakeformation_permissions(create_hybrid_opt_in=True)
        return instance


class ManageAccessForm(forms.ModelForm):
    access_levels = forms.ModelMultipleChoiceField(
        queryset=None,
        template_name="forms/fields/checkbox.html",
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all that apply",
    )

    def __init__(self, *args, **kwargs):
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["access_levels"].queryset = self.grantable_access

    class Meta:
        model = models.TableAccess
        fields = ["access_levels"]

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.revoke_lakeformation_permissions()
        instance.save()
        self.save_m2m()
        instance.grant_lakeformation_permissions()
        return instance
