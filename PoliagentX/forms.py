from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field
from django.core.exceptions import ValidationError
import pandas as pd
import os

def validate_extension(file):
    ext = os.path.splitext(file.name)[1].lower()
    if ext not in ['.xlsx', '.xls']:
        raise ValidationError("Only Excel files (.xlsx, .xls) are allowed.")


def validate_contains_sheet(required_sheet):
    def validator(file):
        ext = os.path.splitext(file.name)[1].lower()
        try:
            if ext == '.xls':
                xl = pd.ExcelFile(file, engine='xlrd')
            elif ext == '.xlsx':
                xl = pd.ExcelFile(file, engine='openpyxl')
            else:
                raise ValidationError("Unsupported file extension.")

            if required_sheet not in xl.sheet_names:
                raise ValidationError(f"The file must contain a sheet named '{required_sheet}'.")
        except ValidationError:
            raise
        except Exception:
            raise ValidationError("Invalid Excel file or unreadable format.")

        return file  # return the file object
    return validator  # return the actual validator function


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
            validate_contains_sheet('template')
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


class Uploaded_expenditure(forms.Form):
    government_expenditure = forms.FileField(
        label='Drag and drop your file here',
        validators=[
            validate_extension,
            lambda f: validate_contains_sheet(f, 'template_expenditure'),
            lambda f: validate_contains_sheet(f, 'template_relation_table')
        ]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field(
                'government_expenditure',
                css_class=(
                    'block w-full text-sm text-gray-500 '
                    'file:mr-4 file:py-2 file:px-4 '
                    'file:rounded-full file:border-0 '
                    'file:text-sm file:font-semibold '
                    'file:bg-violet-50 file:text-violet-700 '
                    'hover:file:bg-violet-100'
                )
            ),
            Submit(
                'submit',
                'Upload',
                css_class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded mt-4'
            )
        )
class Uploaded_interdepenency(forms.Form):
    interdependency_network = forms.FileField(
        label='Drag and drop your file here (Optional)',
        validators=[
            validate_extension,
            lambda f: validate_contains_sheet(f, 'template_expenditure'),
            lambda f: validate_contains_sheet(f, 'template_network')
        ],
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Field(
                'interdependency_network',
                css_class=(
                    'block w-full text-sm text-gray-500 '
                    'file:mr-4 file:py-2 file:px-4 '
                    'file:rounded-full file:border-0 '
                    'file:text-sm file:font-semibold '
                    'file:bg-violet-50 file:text-violet-700 '
                    'hover:file:bg-violet-100'
                )
            ),
            Submit(
                'submit',
                'Upload',
                css_class='bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded mt-4'
            )
        )
