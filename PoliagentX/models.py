from django.db import models
from django.db import models
from pygments.lexers import get_all_lexers
from pygments.styles import get_all_styles


# Create your models here.
class CSVFileUpload(models.Model):
    FILE_TYPE_CHOICES = [
        ('indicators', 'Government Indicators'),
        ('expenditure', 'Government Expenditure'),
        ('interdependencies', 'Interdependencies'),
    ]
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_type = models.CharField(max_length=32, choices=FILE_TYPE_CHOICES)
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'csv_file_uploads'

class GovernmentIndicator(models.Model):
    name = models.CharField(max_length=255)
    value = models.FloatField()
    year = models.IntegerField()
    source_file = models.ForeignKey(CSVFileUpload, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'government_indicators'

class GovernmentExpenditure(models.Model):
    category = models.CharField(max_length=255)
    amount = models.FloatField()
    year = models.IntegerField()
    source_file = models.ForeignKey(CSVFileUpload, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'government_expenditure'

class Interdependency(models.Model):
    from_indicator = models.ForeignKey(
        GovernmentIndicator, on_delete=models.CASCADE, related_name='outgoing_interdependencies', null=True, blank=True
    )
    from_expenditure = models.ForeignKey(
        GovernmentExpenditure, on_delete=models.CASCADE, related_name='outgoing_interdependencies', null=True, blank=True
    )
    to_indicator = models.ForeignKey(
        GovernmentIndicator, on_delete=models.CASCADE, related_name='incoming_interdependencies', null=True, blank=True
    )
    to_expenditure = models.ForeignKey(
        GovernmentExpenditure, on_delete=models.CASCADE, related_name='incoming_interdependencies', null=True, blank=True
    )
    description = models.TextField(blank=True)
    source_file = models.ForeignKey(CSVFileUpload, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'interdependencies'
  
