from rest_framework import serializers
from .models import Government_indicators, Government_expenditure, Interdepencies

class Government_indicators_serializer(serializers.Serializer):
    class Meta:
        model = Government_indicators
        fields = '__all__'
class Government_expenditure_serializer(serializers.Serializer):
    class Meta:
        model = Government_expenditure
        fields = '__all__'
class Interdepencies_serializer(serializers.Serializer):
    class Meta:
        model = Interdepencies
        fields = '__all__'

