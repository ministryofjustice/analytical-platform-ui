import pytest
from django.db import IntegrityError

from ap.users.models import User


@pytest.mark.django_db
class TestUserModel:
    """Test cases for the User model"""

    def test_user_creation_with_lowercase_email(self):
        """Test that user can be created with lowercase email"""
        user = User.objects.create_user(
            email="test@example.com", entra_oid="12345678-1234-1234-1234-123456789012"
        )
        assert user.email == "test@example.com"
        assert user.entra_oid == "12345678-1234-1234-1234-123456789012"

    @pytest.mark.parametrize(
        "input_email,expected_email",
        [
            ("TEST@EXAMPLE.COM", "test@example.com"),
            ("Mixed.Case@EXAMPLE.COM", "mixed.case@example.com"),
            ("CLEAN@EXAMPLE.COM", "clean@example.com"),
        ],
    )
    def test_user_creation_with_email_normalization(self, input_email, expected_email):
        """Test that various email cases are normalized to lowercase on creation"""
        user = User.objects.create_user(
            email=input_email, entra_oid="12345678-1234-1234-1234-123456789012"
        )
        assert user.email == expected_email

    @pytest.mark.parametrize(
        "input_email,expected_email",
        [
            ("MIXED.Case@EXAMPLE.COM", "mixed.case@example.com"),
            ("UPPER@DOMAIN.COM", "upper@domain.com"),
            ("Test.User@Gmail.COM", "test.user@gmail.com"),
        ],
    )
    def test_user_email_normalization_on_save(self, input_email, expected_email):
        """Test that email is normalized when calling save() directly"""
        user = User(email=input_email, entra_oid="12345678-1234-1234-1234-123456789012")
        user.save()
        assert user.email == expected_email

    @pytest.mark.parametrize(
        "input_email,expected_email",
        [
            ("CLEAN@EXAMPLE.COM", "clean@example.com"),
            ("Clean.Test@DOMAIN.ORG", "clean.test@domain.org"),
            ("VALIDATION@TEST.NET", "validation@test.net"),
        ],
    )
    def test_user_email_normalization_on_clean(self, input_email, expected_email):
        """Test that email is normalized when calling clean()"""
        user = User(email=input_email, entra_oid="12345678-1234-1234-1234-123456789012")
        user.clean()
        assert user.email == expected_email

    def test_get_or_create_with_uppercase_email(self):
        """Test that get_or_create normalizes email and finds existing user"""
        # Create user with lowercase email
        User.objects.create_user(
            email="test@example.com", entra_oid="12345678-1234-1234-1234-123456789012"
        )

        # Try to get_or_create with uppercase email - should find existing user
        user, created = User.objects.get_or_create(
            email="TEST@EXAMPLE.COM", defaults={"entra_oid": "87654321-4321-4321-4321-210987654321"}
        )

        assert not created
        assert user.email == "test@example.com"
        assert user.entra_oid == "12345678-1234-1234-1234-123456789012"

    def test_get_or_create_creates_new_user_with_normalized_email(self):
        """Test that get_or_create creates new user with normalized email"""
        user, created = User.objects.get_or_create(
            email="NEW@EXAMPLE.COM", defaults={"entra_oid": "11111111-1111-1111-1111-111111111111"}
        )

        assert created
        assert user.email == "new@example.com"
        assert user.entra_oid == "11111111-1111-1111-1111-111111111111"

    @pytest.mark.parametrize(
        "lookup_email,stored_email,entra_oid",
        [
            ("FIND@EXAMPLE.COM", "find@example.com", "22222222-2222-2222-2222-222222222222"),
            ("FILTER@EXAMPLE.COM", "filter@example.com", "33333333-3333-3333-3333-333333333333"),
        ],
    )
    def test_direct_queryset_methods_with_uppercase_email(
        self, lookup_email, stored_email, entra_oid
    ):
        """Test that direct get() and filter() work with stored lowercase emails"""
        User.objects.create_user(email=stored_email, entra_oid=entra_oid)

        # Test get with exact lowercase match
        user = User.objects.get(email=stored_email)
        assert user.email == stored_email

        # Test filter with exact lowercase match
        users = User.objects.filter(email=stored_email)
        assert users.count() == 1
        assert users.first().email == stored_email

    @pytest.mark.parametrize(
        "lookup_email,stored_email,entra_oid",
        [
            ("EXACT@EXAMPLE.COM", "exact@example.com", "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"),
            (
                "UPPERCASE@EXAMPLE.COM",
                "uppercase@example.com",
                "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
            ),
            ("MiXeD@ExAmPlE.CoM", "mixed@example.com", "cccccccc-cccc-cccc-cccc-cccccccccccc"),
        ],
    )
    def test_get_by_email_case_insensitive(self, lookup_email, stored_email, entra_oid):
        """Test get_by_email with various case combinations"""
        User.objects.create_user(email=stored_email, entra_oid=entra_oid)

        user = User.objects.get_by_email(lookup_email)
        assert user.email == stored_email

    def test_get_by_email_not_found(self):
        """Test get_by_email raises DoesNotExist for non-existent email"""
        with pytest.raises(User.DoesNotExist):
            User.objects.get_by_email("nonexistent@example.com")

    @pytest.mark.parametrize(
        "lookup_email,stored_email,entra_oid",
        [
            ("filter1@example.com", "filter1@example.com", "dddddddd-dddd-dddd-dddd-dddddddddddd"),
            ("FILTER2@EXAMPLE.COM", "filter2@example.com", "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"),
            ("FiLtEr3@ExAmPlE.CoM", "filter3@example.com", "ffffffff-ffff-ffff-ffff-ffffffffffff"),
        ],
    )
    def test_filter_by_email_case_insensitive(self, lookup_email, stored_email, entra_oid):
        """Test filter_by_email with various case combinations"""
        User.objects.create_user(email=stored_email, entra_oid=entra_oid)

        users = User.objects.filter_by_email(lookup_email)
        assert users.count() == 1
        assert users.first().email == stored_email

    def test_filter_by_email_no_results(self):
        """Test filter_by_email returns empty queryset for non-existent email"""
        users = User.objects.filter_by_email("nonexistent@example.com")
        assert users.count() == 0

    def test_filter_by_email_multiple_users_different_emails(self):
        """Test filter_by_email with multiple users having different emails"""
        User.objects.create_user(
            email="user1@example.com", entra_oid="11111111-1111-1111-1111-111111111111"
        )
        User.objects.create_user(
            email="user2@example.com", entra_oid="22222222-2222-2222-2222-222222222222"
        )

        users = User.objects.filter_by_email("USER1@EXAMPLE.COM")
        assert users.count() == 1
        assert users.first().email == "user1@example.com"

    def test_entra_oid_uniqueness(self):
        """Test that entra_oid must be unique"""
        User.objects.create_user(
            email="user1@example.com", entra_oid="44444444-4444-4444-4444-444444444444"
        )

        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email="user2@example.com",
                entra_oid="44444444-4444-4444-4444-444444444444",  # Same oid
            )

    def test_get_by_entra_oid_method(self):
        """Test the get_by_entra_oid convenience method"""
        user = User.objects.create_user(
            email="getbyoid@example.com", entra_oid="55555555-5555-5555-5555-555555555555"
        )

        found_user = User.get_by_entra_oid("55555555-5555-5555-5555-555555555555")
        assert found_user == user
        assert found_user.email == "getbyoid@example.com"

    def test_get_by_entra_oid_not_found(self):
        """Test that get_by_entra_oid raises DoesNotExist for non-existent oid"""
        with pytest.raises(User.DoesNotExist):
            User.get_by_entra_oid("nonexistent-oid")

    def test_user_str_method(self):
        """Test the __str__ method returns email"""
        user = User(email="str@example.com")
        assert str(user) == "str@example.com"

    def test_user_repr_method(self):
        """Test the __repr__ method"""
        user = User(email="repr@example.com", entra_oid="66666666-6666-6666-6666-666666666666")
        # Note: username is None since we removed it, so __repr__ shows None
        expected = "<User: None (66666666-6666-6666-6666-666666666666)>"
        assert repr(user) == expected

    def test_django_auto_pk_is_used(self):
        """Test that Django's auto-incrementing primary key is used"""
        user = User.objects.create_user(
            email="pk@example.com", entra_oid="77777777-7777-7777-7777-777777777777"
        )

        # Django auto PK should be an integer
        assert isinstance(user.pk, int)
        assert user.pk is not None
        assert user.pk > 0

        # entra_oid should be separate from PK
        assert user.entra_oid == "77777777-7777-7777-7777-777777777777"
        assert user.pk != user.entra_oid

    def test_empty_email_handled_gracefully(self):
        """Test that empty email doesn't cause issues"""
        user = User(email="", entra_oid="88888888-8888-8888-8888-888888888888")
        user.save()
        assert user.email == ""

    def test_create_superuser_with_normalized_email(self):
        """Test that create_superuser normalizes email"""
        user = User.objects.create_superuser(
            email="ADMIN@EXAMPLE.COM",
            password="testpass",
            entra_oid="99999999-9999-9999-9999-999999999999",
        )
        assert user.email == "admin@example.com"
        assert user.is_superuser is True
        assert user.is_staff is True

    def test_email_is_required(self):
        """Test that email is required - None email should raise IntegrityError"""
        with pytest.raises(IntegrityError):
            user = User(email=None, entra_oid="99999999-9999-9999-9999-999999999999")
            user.save()

    def test_email_as_username_field(self):
        """Test that email is used as the USERNAME_FIELD"""
        assert User.USERNAME_FIELD == "email"
        assert User.REQUIRED_FIELDS == []

    def test_username_field_is_none(self):
        """Test that username field is removed"""
        user = User.objects.create_user(
            email="test@example.com", entra_oid="12345678-1234-1234-1234-123456789012"
        )
        assert user.username is None
        assert not hasattr(User, "username") or User.username is None
