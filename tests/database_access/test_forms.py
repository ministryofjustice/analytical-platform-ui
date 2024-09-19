from django import forms

from ap.database_access.forms import AccessForm


class TestAccessForm:

    def create_form(self, users, form_data, table_name, database_name, grantable_access=None):
        form = AccessForm(
            data=form_data,
            table_name=table_name,
            database_name=database_name,
            grantable_access=grantable_access,
        )

        form.cleaned_data = {"user": users["normal_user"]}

        return form

    def test_clean_user(self, users, permissions, table_access):
        form_data = {
            "user": users["normal_user"],
            "permissions": [permissions["select_table"]],
            "grantable_permissions": [],
        }

        form = self.create_form(users, form_data, "table_3", "test_db_1")
        user = form.clean_user()
        assert user == users["normal_user"]

    def test_clean_user_duplicate_table_name(self, users, permissions, table_access):
        """Tests that user is returned even though name exists in a different"""
        form_data = {
            "user": users["normal_user"],
            "permissions": [permissions["select_table"]],
            "grantable_permissions": [],
        }

        form = self.create_form(users, form_data, "table_1", "test_db_2")
        user = form.clean_user()
        assert user == users["normal_user"]

    def test_clean_user_duplicate(self, users, permissions, table_access):
        """Tests that validation error is raised if duplicate table name and database name"""
        form_data = {
            "user": users["normal_user"],
            "permissions": [permissions["select_table"]],
            "grantable_permissions": [],
        }

        form = self.create_form(users, form_data, "table_1", "test_db_1")

        try:
            form.clean_user()
            AssertionError("Should Fail")
        except forms.ValidationError:
            assert True
