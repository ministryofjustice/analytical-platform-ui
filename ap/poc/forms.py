from django import forms


class CreateDataFilterForm(forms.Form):
    name = forms.CharField(label="Data Filter Name", max_length=100)
    include_columns = forms.MultipleChoiceField(
        label="Include Columns", widget=forms.CheckboxSelectMultiple, required=False
    )
    row_filter_expression = forms.CharField(label="Row Filter Expression")
