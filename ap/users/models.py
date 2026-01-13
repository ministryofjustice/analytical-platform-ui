from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models

from ap.aws.iam import IAMService
from ap.aws.identitystore import IdentityStore
from ap.core.utils import sanitize_dns_label


class UserManager(BaseUserManager):
    def get_or_create(self, defaults=None, **kwargs):
        # Normalize email in lookup kwargs
        if "email" in kwargs and kwargs["email"]:
            kwargs["email"] = kwargs["email"].lower()

        # Normalize email in defaults
        if defaults and "email" in defaults and defaults["email"]:
            defaults["email"] = defaults["email"].lower()

        return super().get_or_create(defaults=defaults, **kwargs)

    def create_user(self, email=None, password=None, **extra_fields):
        # Normalize email before creating user

        if not email:
            raise ValueError("The Email field must be set")

        email = email.lower()
        user = self.model(email=email.lower(), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)

    def get_by_email(self, email):
        """Get user by email (case-insensitive)"""
        return self.get(email__iexact=email)

    def filter_by_email(self, email):
        """Filter users by email (case-insensitive)"""
        return self.filter(email__iexact=email)


class User(AbstractUser):
    entra_oid = models.CharField(
        max_length=128,
        unique=True,
        db_index=True,
        help_text="EntraID Object Identifier",
        blank=True,
        null=True,
    )
    username = None
    email = models.EmailField(unique=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "ap_user"
        ordering = ("email",)

    def __repr__(self):
        return f"<User: {self.username} ({self.entra_oid})>"

    def __str__(self) -> str:
        return self.email

    @staticmethod
    def construct_username(name):
        return sanitize_dns_label(name)

    @classmethod
    def get_by_entra_oid(cls, oid):
        """Convenience method to find user by EntraID OID"""
        return cls.objects.get(entra_oid=oid)

    def clean(self):
        """Normalize email to lowercase"""
        super().clean()
        if self.email:
            self.email = self.email.lower()

    def create_iam_role(self):
        iamservice = IAMService()
        iamservice.create_role(
            role_name=self.entra_oid, path="/users/", description=f"Role for user {self.email}"
        )
        iamservice.attach_role_policy(
            role_name=self.entra_oid, policy_arn=settings.POC_USER_POLICY_ARN
        )

    def add_user_to_group(self, group_name):
        identity_store = IdentityStore(
            settings.IDENTITY_CENTER_ASSUMED_ROLE,
            "APUIIdentityCenterAccess",
            settings.IDENTITY_CENTER_ACCOUNT_REGION,
        )

        identity_store.add_user_to_group(self.email, group_name)

    def remove_user_from_group(self, group_name):
        identity_store = IdentityStore(
            settings.IDENTITY_CENTER_ASSUMED_ROLE,
            "APUIIdentityCenterAccess",
            settings.IDENTITY_CENTER_ACCOUNT_REGION,
        )
        identity_store.remove_user_from_group(self.email, group_name)

    def initialise_aws_access(self):
        """Initialises AWS access for the user by creating IAM role and adding to group"""
        self.create_iam_role()
        # self.add_user_to_group(settings.POC_GROUP_NAME)

    def save(self, *args, **kwargs):
        # Ensure email is lowercase before saving
        if self.email:
            self.email = self.email.lower()

        return super().save(*args, **kwargs)
