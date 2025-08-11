from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from django.core.exceptions import ValidationError
import pandas as pd
import os

def validate_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.xlsx', '.xls', '.csv']:
        raise ValidationError("Only Excel files (.xlsx, .xls, .csv) are allowed.")


def validate_contains_sheet(file, required_sheet):
    ext = os.path.splitext(file.name)[1].lower()

    # Rewind the file pointer before reading
    file.seek(0)

    try:
        if ext == '.xls':
            xl = pd.ExcelFile(file, engine='xlrd')  # Requires xlrd==1.2.0
        elif ext == '.xlsx':
            xl = pd.ExcelFile(file, engine='openpyxl')
        else:
            raise ValidationError("Unsupported file")

        # Sheet existence check
        if required_sheet not in xl.sheet_names:
            raise ValidationError(f"The file uploaded does not contain a sheet named '{required_sheet}'.")

    except ValidationError:
        # Re-raise custom messages (e.g., missing sheet or bad extension)
        raise
    except Exception as e:
        # Catch other unreadable/corrupt file errors
        raise ValidationError("Invalid Excel file or unreadable format.")


    
class Uploaded_indicators(forms.Form):
    government_indicators = forms.FileField(
        label='Upload file',
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'id': 'file-upload',  
            'class': 'hidden'
        }),
        validators=[
            validate_extension,
            lambda f: validate_contains_sheet(f, 'template')
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field(
                'government_indicators',
                id='file-upload',  
                css_class='hidden'
            ),
            Submit(
                'submit',
                'Upload',
                css_class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded mt-4'
            )
        )

class BudgetForm(forms.Form):
    budget = forms.IntegerField(label="Enter Budget (in local currency)", min_value=0)
    inflation_rate = forms.FloatField(label="Inflation Rate (%)", min_value=0)
    


class Uploaded_Budget(forms.Form):
    government_expenditure = forms.FileField(
        label='Upload file',
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'id': 'id_government_expenditure',
            'class': 'hidden'
        }),
        validators=[
            validate_extension,
            lambda e: validate_contains_sheet(e, 'template_budget'),
            lambda e: validate_contains_sheet(e, 'template_relation')
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field(
                'government_expenditure',
                id='file-upload',  
                css_class='hidden'
            ),
            Submit(
                'submit',
                'Upload',
                css_class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded mt-4'
            )
        )


class Uploaded_networks(forms.Form):
    interdependency_network = forms.FileField(
        label='Upload file',
        required=True,
        widget=forms.ClearableFileInput(attrs={
            'id': 'file-upload',  
            'class': 'hidden'
        }),
        validators=[
            validate_extension
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field(
                'interdependency_network',
                id='file-upload',  
                css_class='hidden'
            ),
            Submit(
                'submit',
                'Upload',
                css_class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded mt-4'
            )
        )
