from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from django.core.exceptions import ValidationError
from django.utils import timezone


class TagSettingsForm(forms.Form):
    formula = forms.ChoiceField(choices=[("mean", "Mean"), ("median", "Median")], initial="mean",)
    access_token = forms.CharField()
    start_date = forms.DateField(widget=forms.widgets.DateInput(
        attrs={'type': 'date',
               'value': (timezone.now() - timezone.timedelta(days=365*2)).strftime("%Y-%m-%d")}
    ))
    end_date = forms.DateField(widget=forms.widgets.DateInput(
        attrs={'type': 'date',
               'value': (timezone.now() - timezone.timedelta(days=1)).strftime("%Y-%m-%d")}
    ))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'form'
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            'access_token',
            Row(
                Column('start_date', css_class='form-group col-md-6 mb-0'),
                Column('end_date', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Row(Column('formula', css_class='form-group col-md-2 mb-0'), css_class='form_row'),
            Submit('submit', 'Submit')
        )


    def clean(self):
        start_date = self.cleaned_data.get('start_date')
        end_date = self.cleaned_data.get('end_date')

        if start_date and end_date and end_date < start_date:
            raise ValidationError("End date cant be earlier than start date")

    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        if start_date >= timezone.now().date():
            raise ValidationError("Start date must be earlier than today")
        return start_date

    def clean_end_date(self):
        end_date = self.cleaned_data['end_date']
        if end_date >= timezone.now().date():
            raise ValidationError("End date must be earlier than today")

        return end_date

