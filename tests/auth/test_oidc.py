import pytest

from controlpanel.auth import OIDCSubAuthenticationBackend


class TestOIDCSubAuthenticationBackend:
    @pytest.mark.django_db
    def test_create_user(self):
        token = {
            "userinfo": {"oid": "testing_new", "name": "testing_name", "email": "testing_email"}
        }
        test_instance = OIDCSubAuthenticationBackend(token)
        user = test_instance.create_or_update_user()
        assert user.name == "testing_name"

    @pytest.mark.django_db
    def test_update_user(self, users):
        token = {
            "userinfo": {
                "oid": users["normal_user"],
                "name": "testing_new_name",
                "email": "testing_new_email",
            }
        }
        test_instance = OIDCSubAuthenticationBackend(token)
        user = test_instance.create_or_update_user()
        assert user.name == "testing_new_name"
