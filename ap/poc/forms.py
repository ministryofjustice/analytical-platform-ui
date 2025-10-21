from django import forms


class CreateDataFilterForm(forms.Form):
    name = forms.CharField(
        label="Data Filter Name",
        max_length=100,
        widget=forms.TextInput(attrs={"class": "govuk-input"}),
        required=True,
    )
    include_columns = forms.MultipleChoiceField(
        label="Include Columns",
        widget=forms.CheckboxSelectMultiple(attrs={"class": "govuk-checkboxes__input"}),
        required=False,
    )
    row_filter_expression = forms.CharField(
        label="Row Filter Expression",
        widget=forms.TextInput(attrs={"class": "govuk-input"}),
        required=False,
    )


class UserChoiceForm(forms.Form):
    user_email = forms.ChoiceField(
        label="User Email",
        choices=[],
        widget=forms.Select(
            attrs={
                "class": "govuk-select",
                "aria-label": "Select user email",
            }
        ),
        required=True,
    )

    def __init__(self, users, *args, **kwargs):
        super().__init__(*args, **kwargs)

        user_choices = [("", "Select a user...")]

        # Add user choices
        user_choices.extend([(user.email, user.email) for user in users])

        self.fields["user_email"].choices = user_choices
