from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django.core.exceptions import ValidationError
from django.utils import timezone


class TagSettingsForm(forms.Form):
    formula = forms.ChoiceField(choices=[("mean", "Mean"), ("median", "Median")], initial="mean",)
    access_token = forms.CharField()
    start_date = forms.DateField(input_formats=['%d-%m-%Y'],
                                 widget=forms.DateInput(
        attrs={'class': 'datepicker', 'value': (timezone.now() - timezone.timedelta(days=365*2)).strftime("%d-%m-%Y")})
                                 )

    end_date = forms.DateField(input_formats=['%d-%m-%Y'],
                               widget=forms.DateInput(
        attrs={'class': 'datepicker', 'value': (timezone.now() - timezone.timedelta(days=1)).strftime("%d-%m-%Y")}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_id = 'form'
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Submit'))

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

