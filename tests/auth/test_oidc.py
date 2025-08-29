import pytest

from ap.auth.oidc import OIDCSubAuthenticationBackend


class TestOIDCSubAuthenticationBackend:
    @pytest.mark.django_db
    def test_create_user(self):
        token = {"userinfo": {"oid": "testing_new", "email": "testing_email"}}
        test_instance = OIDCSubAuthenticationBackend(token)
        user = test_instance.create_or_update_user()
        assert user.email == "testing_email"

    @pytest.mark.django_db
    def test_update_user(self, users):
        token = {
            "userinfo": {
                "oid": users["normal_user"],
                "email": "testing_new_email",
            }
        }
        test_instance = OIDCSubAuthenticationBackend(token)
        user = test_instance.create_or_update_user()
        assert user.email == "testing_new_email"
