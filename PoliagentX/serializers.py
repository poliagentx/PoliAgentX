from rest_framework import serializers
# # from .models import GovernmentIndicator, GovernmentExpenditure, Interdependency
# from django.core.validators import FileExtensionValidator
# from django.conf import settings

# # Get upload size limit from settings, default to 10MB
# MAX_UPLOAD_SIZE = getattr(settings, 'MAX_UPLOAD_SIZE', 10 * 1024 * 1024)

# # --- Model Serializers ---
# class GovernmentIndicatorSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = GovernmentIndicator
#         fields = '__all__'
#         read_only_fields = ('id', 'created_at')  # Auto-generated fields

# class GovernmentExpenditureSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = GovernmentExpenditure
#         fields = '__all__'
#         read_only_fields = ('id', 'created_at')

# class InterdependencySerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Interdependency
#         fields = '__all__'
#         read_only_fields = ('id', 'created_at')

# # --- File Upload Serializer ---
# class WorkflowFileUploadSerializer(serializers.Serializer):
#     expenditure_file = serializers.FileField()
#     indicators_file = serializers.FileField()
    
#     def validate(self, attrs):
#         """Custom validation for uploaded files"""
#         # Check file size using settings
        # if attrs['expenditure_file'].size > MAX_UPLOAD_SIZE:
        #     raise serializers.ValidationError({
        #         'expenditure_file': f'File size must be under {MAX_UPLOAD_SIZE // (1024*1024)}MB'
        #     })
        
        # if attrs['indicators_file'].size > MAX_UPLOAD_SIZE:
        #     raise serializers.ValidationError({
        #         'indicators_file': f'File size must be under {MAX_UPLOAD_SIZE // (1024*1024)}MB'
        #     })
        
        # return attrs

# # --- API Response Serializers ---
# class WorkflowResponseSerializer(serializers.Serializer):
#     message = serializers.CharField(read_only=True)
#     run_id = serializers.CharField(read_only=True)
#     progress = serializers.DictField(read_only=True)
#     outputs = serializers.DictField(read_only=True)

# class WorkflowStatusSerializer(serializers.Serializer):
#     run_id = serializers.CharField(read_only=True)
#     status = serializers.CharField(read_only=True)
#     files = serializers.DictField(read_only=True)

# class ErrorResponseSerializer(serializers.Serializer):
#     error = serializers.CharField(read_only=True)

# # --- Additional Utility Serializers ---
# class FileUploadResponseSerializer(serializers.Serializer):
#     """Serializer for file upload confirmation"""
#     message = serializers.CharField(read_only=True)
#     file_id = serializers.CharField(read_only=True)
#     filename = serializers.CharField(read_only=True)
#     file_size = serializers.IntegerField(read_only=True)

# class ProcessingStatusSerializer(serializers.Serializer):
#     """Serializer for processing status updates"""
#     job_id = serializers.CharField(read_only=True)
#     status = serializers.ChoiceField(
#         choices=[
#             ('pending', 'Pending'),
#             ('processing', 'Processing'),
#             ('completed', 'Completed'),
#             ('failed', 'Failed')
#         ],
#         read_only=True
#     )
#     progress_percentage = serializers.IntegerField(read_only=True)
#     current_step = serializers.CharField(read_only=True)
#     estimated_time_remaining = serializers.CharField(read_only=True, allow_null=True)
