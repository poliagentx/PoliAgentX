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
    
    # Additional fields for bottleneck analysis
    series_code = models.CharField(max_length=100, blank=True)
    sdg = models.CharField(max_length=50, blank=True)
    instrumental = models.BooleanField(default=False)
    color = models.CharField(max_length=20, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'government_indicators'
        
    def __str__(self):
        return f"{self.name} ({self.year})"

class GovernmentExpenditure(models.Model):
    category = models.CharField(max_length=255)
    amount = models.FloatField()
    year = models.IntegerField()
    source_file = models.ForeignKey(CSVFileUpload, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Additional fields
    sdg = models.CharField(max_length=50, blank=True)
    programme_code = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'government_expenditure'
        
    def __str__(self):
        return f"{self.category} - {self.year}"

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

class WorkflowRun(models.Model):
    """Track complete workflow executions"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('preparing', 'Preparing Data'),
        ('calibrating', 'Calibrating Model'),
        ('simulating', 'Running Simulation'),
        ('analyzing_bottlenecks', 'Analyzing Bottlenecks'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    run_id = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    # Input files
    expenditure_file = models.ForeignKey(CSVFileUpload, on_delete=models.SET_NULL, null=True, blank=True, related_name='expenditure_workflows')
    indicators_file = models.ForeignKey(CSVFileUpload, on_delete=models.CASCADE, related_name='indicator_workflows')
    
    # Output paths
    output_directory = models.CharField(max_length=500)
    error_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'workflow_runs'

class BottleneckAnalysis(models.Model):
    """Store bottleneck analysis results"""
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name='bottleneck_analyses')
    
    # Results summary
    bottleneck_count = models.IntegerField()
    total_indicators = models.IntegerField()
    
    # File paths
    results_csv_path = models.CharField(max_length=500)
    development_gaps_plot_path = models.CharField(max_length=500)
    gap_reduction_plot_path = models.CharField(max_length=500)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bottleneck_analyses'

class AnalysisResult(models.Model):
    """Store detailed analysis results"""
    workflow_run = models.ForeignKey(WorkflowRun, on_delete=models.CASCADE, related_name='analysis_results')
    
    # Indicator-specific results
    indicator = models.ForeignKey(GovernmentIndicator, on_delete=models.CASCADE, null=True, blank=True)
    series_code = models.CharField(max_length=100)
    sdg = models.CharField(max_length=50)
    
    # Analysis values
    goal = models.FloatField()
    baseline_final = models.FloatField()
    frontier_final = models.FloatField()
    gap_base = models.FloatField()
    gap_frontier = models.FloatField()
    gap_reduction = models.FloatField()
    historical_performance = models.FloatField()
    is_bottleneck = models.BooleanField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'analysis_results'
        
    def __str__(self):
        return f"{self.series_code} - Gap Reduction: {self.gap_reduction:.2f}"
  
