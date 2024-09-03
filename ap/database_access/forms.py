from django import forms
from django.db import transaction

import botocore
import structlog

from ap.users.models import User

from . import models

logger = structlog.get_logger(__name__)


class AccessForm(forms.ModelForm):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        label="Select a user to grant access to",
        template_name="forms/fields/select.html",
    )
    permissions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        template_name="forms/fields/checkbox.html",
        help_text="Select all that apply",
        required=True,
    )
    grantable_permissions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        template_name="forms/fields/checkbox.html",
        help_text="Select all that apply",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.table_name = kwargs.pop("table_name")
        self.database_name = kwargs.pop("database_name")
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = self.grantable_access
        self.fields["grantable_permissions"].queryset = self.grantable_access

    class Meta:
        model = models.TableAccess
        fields = ["permissions", "grantable_permissions"]

    def clean_user(self):
        user = self.cleaned_data.get("user")
        try:
            self._meta.model.objects.get(name=self.table_name, database_access__user=user)
            raise forms.ValidationError("Selected user already has access to this table.")
        except self._meta.model.DoesNotExist:
            pass

        return user

    @transaction.atomic
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
    permissions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        template_name="forms/fields/checkbox.html",
        help_text="Select all that apply",
        required=True,
    )
    grantable_permissions = forms.ModelMultipleChoiceField(
        queryset=None,
        widget=forms.CheckboxSelectMultiple,
        template_name="forms/fields/checkbox.html",
        help_text="Select all that apply",
        required=False,
    )

    class Meta:
        model = models.TableAccess
        fields = ["permissions", "grantable_permissions"]

    def __init__(self, *args, **kwargs):
        self.grantable_access = kwargs.pop("grantable_access")
        super().__init__(*args, **kwargs)
        self.fields["permissions"].queryset = self.grantable_access
        self.fields["grantable_permissions"].queryset = self.grantable_access

    def clean(self):
        cleaned_data = super().clean()

        grantable_permissions = cleaned_data.get("grantable_permissions", [])
        if not grantable_permissions:
            return cleaned_data

        permissions = cleaned_data.get("permissions", [])
        for grantable_permission in grantable_permissions:
            if grantable_permission not in permissions:
                self.add_error(
                    "grantable_permissions",
                    f"{grantable_permission} is not a part of the selected grantable permissions.",
                )

        return cleaned_data

    def save(self, commit=True):
        try:
            with transaction.atomic():
                instance = super().save(commit=False)
                instance.revoke_lakeformation_permissions()
                instance.save()
                self.save_m2m()
                instance.grant_lakeformation_permissions()
                return instance
        except botocore.exceptions.ClientError as error:
            logger.info("Updating permissions failed, restoring original permissions", error=error)
            instance.grant_lakeformation_permissions()
            raise error
