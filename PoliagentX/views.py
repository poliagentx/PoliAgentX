from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import os
from django.conf import settings
from datetime import datetime
import uuid
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse
from .serializers import (
    WorkflowFileUploadSerializer, 
    WorkflowResponseSerializer, 
    WorkflowStatusSerializer,
    ErrorResponseSerializer,
)
from PoliagentX.backend_poliagentx.data_preparation_expenditure import prepare_expenditure_data
from PoliagentX.backend_poliagentx.data_preparation_indicators import prepare_indicators
from PoliagentX.backend_poliagentx.data_preparation_interdependencies import prepare_interdependencies
from PoliagentX.backend_poliagentx.model_calibration import calibrate_model
from PoliagentX.backend_poliagentx.simple_prospective_simulation import run_simulation
from PoliagentX.backend_poliagentx.structural_bottlenecks import analyze_structural_bottlenecks




def save_uploaded_file(file, path):
    with open(path, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

def generate_run_id():
    return datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + str(uuid.uuid4())[:8]

def format_error_response(message, status_code=status.HTTP_400_BAD_REQUEST):
    serializer = ErrorResponseSerializer(data={'error': str(message)})
    serializer.is_valid(raise_exception=True)
    return Response(serializer.data, status=status_code)

class CompleteWorkflowView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        try:
            run_id = generate_run_id()
            serializer = WorkflowFileUploadSerializer(data=request.data, files=request.FILES)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            exp_file = serializer.validated_data['expenditure_file']
            indi_file = serializer.validated_data['indicators_file']

            temp_dir = os.path.join(settings.MEDIA_ROOT, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            temp_exp_path = os.path.join(temp_dir, f'exp_{run_id}.csv')
            temp_indi_path = os.path.join(temp_dir, f'indi_{run_id}.csv')
            save_uploaded_file(exp_file, temp_exp_path)
            save_uploaded_file(indi_file, temp_indi_path)

            run_output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs', run_id)
            os.makedirs(run_output_dir, exist_ok=True)
            output_exp_path = os.path.join(run_output_dir, 'data_expenditure.csv')
            output_rel_path = os.path.join(run_output_dir, 'data_relational_table.csv')
            output_indi_path = os.path.join(run_output_dir, 'data_indicators.csv')
            output_network_path = os.path.join(run_output_dir, 'data_network.csv')
            output_params_path = os.path.join(run_output_dir, 'parameters.csv')
            output_simulation_dir = os.path.join(run_output_dir, 'simulation')
            os.makedirs(output_simulation_dir, exist_ok=True)

            progress = {'step': 'starting', 'message': 'Initializing workflow...'}
            progress['step'] = 'preparing_data'
            progress['message'] = 'Preparing expenditure data...'
            prepare_expenditure_data(temp_exp_path, temp_indi_path, output_exp_path, output_rel_path)
            progress['message'] = 'Preparing indicators data...'
            prepare_indicators(temp_indi_path, output_indi_path)
            progress['message'] = 'Preparing interdependencies...'
            prepare_interdependencies(output_indi_path, output_network_path)

            progress['step'] = 'calibrating'
            progress['message'] = 'Calibrating model...'
            calibrate_model(output_indi_path, output_network_path, output_exp_path, output_rel_path, output_params_path)

            progress['step'] = 'simulating'
            progress['message'] = 'Running simulation...'
            simulation_output = run_simulation(output_indi_path, output_params_path, output_network_path, output_exp_path, output_rel_path, output_simulation_dir)

            progress['step'] = 'analyzing_bottlenecks'
            progress['message'] = 'Analyzing structural bottlenecks...'
            bottleneck_output_dir = os.path.join(run_output_dir, 'bottleneck_analysis')
            bottleneck_results = analyze_structural_bottlenecks(
                output_indi_path, output_params_path, output_network_path,
                output_exp_path, output_rel_path, bottleneck_output_dir
            )

            progress['step'] = 'completed'
            progress['message'] = 'Workflow completed successfully!'

            response_data = {
                'message': 'Complete workflow finished!',
                'run_id': run_id,
                'progress': progress,
                'outputs': {
                    'expenditure': output_exp_path,
                    'relational_table': output_rel_path,
                    'indicators': output_indi_path,
                    'network': output_network_path,
                    'parameters': output_params_path,
                    'simulation': simulation_output,
                    'bottleneck_analysis': bottleneck_results
                }
            }

            response_serializer = WorkflowResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            return format_error_response(e)

class BottleneckAnalysisView(APIView):
    def post(self, request):
        try:
            indicators_path = request.data.get('indicators_path')
            parameters_path = request.data.get('parameters_path')
            network_path = request.data.get('network_path')
            expenditure_path = request.data.get('expenditure_path')
            relational_table_path = request.data.get('relational_table_path')

            run_id = generate_run_id()
            output_dir = os.path.join(settings.MEDIA_ROOT, 'outputs', run_id, 'bottleneck_analysis')

            results = analyze_structural_bottlenecks(
                indicators_path, parameters_path, network_path,
                expenditure_path, relational_table_path, output_dir
            )

            return Response({
                'message': 'Bottleneck analysis completed!',
                'run_id': run_id,
                'results': results
            }, status=status.HTTP_200_OK)

        except Exception as e:
            return format_error_response(e)

class DownloadResultView(APIView):
    def get(self, request, run_id, file_type):
        try:
            file_paths = {
                'expenditure': f'outputs/{run_id}/data_expenditure.csv',
                'indicators': f'outputs/{run_id}/data_indicators.csv',
                'network': f'outputs/{run_id}/data_network.csv',
                'parameters': f'outputs/{run_id}/parameters.csv',
                'simulation': f'outputs/{run_id}/simulation/simulation_output.csv',
                'development_plot': f'outputs/{run_id}/bottleneck_analysis/development_gaps_comparison.png',
                'gap_plot': f'outputs/{run_id}/bottleneck_analysis/gap_reduction_analysis.png',
                'bottleneck_csv': f'outputs/{run_id}/bottleneck_analysis/bottleneck_analysis_results.csv',
            }

            if file_type in file_paths:
                file_path = os.path.join(settings.MEDIA_ROOT, file_paths[file_type])
                if os.path.exists(file_path):
                    return FileResponse(open(file_path, 'rb'))

            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return format_error_response(e)

class WorkflowStatusView(APIView):
    def get(self, request, run_id):
        try:
            run_dir = os.path.join(settings.MEDIA_ROOT, 'outputs', run_id)
            if os.path.exists(run_dir):
                files = {
                    'expenditure': os.path.exists(os.path.join(run_dir, 'data_expenditure.csv')),
                    'indicators': os.path.exists(os.path.join(run_dir, 'data_indicators.csv')),
                    'network': os.path.exists(os.path.join(run_dir, 'data_network.csv')),
                    'parameters': os.path.exists(os.path.join(run_dir, 'parameters.csv')),
                    'simulation': os.path.exists(os.path.join(run_dir, 'simulation')),
                }

                status_data = {
                    'run_id': run_id,
                    'status': 'completed' if all(files.values()) else 'in_progress',
                    'files': files
                }

                status_serializer = WorkflowStatusSerializer(data=status_data)
                status_serializer.is_valid(raise_exception=True)
                return Response(status_serializer.data)

            return format_error_response('Run not found', status_code=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return format_error_response(e)
