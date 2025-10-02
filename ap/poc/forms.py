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
