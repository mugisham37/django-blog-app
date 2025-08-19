"""
Bulk operations utilities for efficient data management.
"""

from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.db.models import Q
from typing import List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BulkOperationMixin:
    """Mixin to add bulk operations to ViewSets."""
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create multiple objects in a single request."""
        data = request.data
        
        if not isinstance(data, list):
            return Response(
                {'error': 'Expected a list of objects'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(data) > 100:  # Limit bulk operations
            return Response(
                {'error': 'Maximum 100 objects allowed per bulk operation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=data, many=True)
        
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    instances = serializer.save()
                    return Response(
                        self.get_serializer(instances, many=True).data,
                        status=status.HTTP_201_CREATED
                    )
            except IntegrityError as e:
                return Response(
                    {'error': f'Database integrity error: {str(e)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'])
    def bulk_update(self, request):
        """Update multiple objects in a single request."""
        data = request.data
        
        if not isinstance(data, list):
            return Response(
                {'error': 'Expected a list of objects'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(data) > 100:
            return Response(
                {'error': 'Maximum 100 objects allowed per bulk operation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updated_objects = []
        errors = []
        
        try:
            with transaction.atomic():
                for item_data in data:
                    if 'id' not in item_data:
                        errors.append({'error': 'ID is required for updates'})
                        continue
                    
                    try:
                        instance = self.get_queryset().get(pk=item_data['id'])
                        serializer = self.get_serializer(
                            instance, data=item_data, partial=True
                        )
                        
                        if serializer.is_valid():
                            updated_instance = serializer.save()
                            updated_objects.append(updated_instance)
                        else:
                            errors.append({
                                'id': item_data['id'],
                                'errors': serializer.errors
                            })
                    except self.queryset.model.DoesNotExist:
                        errors.append({
                            'id': item_data['id'],
                            'error': 'Object not found'
                        })
                
                if errors:
                    return Response(
                        {'errors': errors},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                return Response(
                    self.get_serializer(updated_objects, many=True).data,
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            logger.error(f"Bulk update error: {str(e)}")
            return Response(
                {'error': 'Bulk update failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['delete'])
    def bulk_delete(self, request):
        """Delete multiple objects in a single request."""
        ids = request.data.get('ids', [])
        
        if not isinstance(ids, list):
            return Response(
                {'error': 'Expected a list of IDs'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(ids) > 100:
            return Response(
                {'error': 'Maximum 100 objects allowed per bulk operation'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                queryset = self.get_queryset().filter(id__in=ids)
                deleted_count = queryset.count()
                queryset.delete()
                
                return Response(
                    {'deleted_count': deleted_count},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            logger.error(f"Bulk delete error: {str(e)}")
            return Response(
                {'error': 'Bulk delete failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BulkSerializer(serializers.ListSerializer):
    """Custom list serializer for bulk operations."""
    
    def create(self, validated_data):
        """Create multiple instances efficiently."""
        model_class = self.child.Meta.model
        instances = []
        
        for item_data in validated_data:
            instances.append(model_class(**item_data))
        
        # Use bulk_create for efficiency
        return model_class.objects.bulk_create(instances)
    
    def update(self, instance, validated_data):
        """Update multiple instances efficiently."""
        # This is more complex as bulk_update requires specific fields
        # For now, we'll update individually but within a transaction
        updated_instances = []
        
        for item_data in validated_data:
            if 'id' in item_data:
                try:
                    obj = instance.get(pk=item_data['id'])
                    for attr, value in item_data.items():
                        if attr != 'id':
                            setattr(obj, attr, value)
                    obj.save()
                    updated_instances.append(obj)
                except instance.model.DoesNotExist:
                    continue
        
        return updated_instances


class BulkOperationValidator:
    """Validator for bulk operations."""
    
    @staticmethod
    def validate_bulk_data(data: List[Dict[str, Any]], max_items: int = 100) -> Dict[str, Any]:
        """Validate bulk operation data."""
        errors = []
        
        if not isinstance(data, list):
            return {'valid': False, 'error': 'Expected a list of objects'}
        
        if len(data) == 0:
            return {'valid': False, 'error': 'Empty data list'}
        
        if len(data) > max_items:
            return {
                'valid': False, 
                'error': f'Maximum {max_items} objects allowed per bulk operation'
            }
        
        # Validate each item has required fields
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                errors.append(f'Item {i}: Expected object, got {type(item).__name__}')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {'valid': True}
    
    @staticmethod
    def validate_bulk_update_data(data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate bulk update data."""
        base_validation = BulkOperationValidator.validate_bulk_data(data)
        if not base_validation['valid']:
            return base_validation
        
        errors = []
        
        # Check that all items have IDs for updates
        for i, item in enumerate(data):
            if 'id' not in item:
                errors.append(f'Item {i}: ID is required for updates')
        
        if errors:
            return {'valid': False, 'errors': errors}
        
        return {'valid': True}


class BulkQueryManager:
    """Manager for efficient bulk queries."""
    
    @staticmethod
    def bulk_get_or_create(model_class, data_list, unique_fields):
        """Efficiently get or create multiple objects."""
        existing_objects = {}
        new_objects = []
        
        # Build query for existing objects
        q_objects = Q()
        for data in data_list:
            q_filter = Q()
            for field in unique_fields:
                if field in data:
                    q_filter &= Q(**{field: data[field]})
            q_objects |= q_filter
        
        # Get existing objects
        if q_objects:
            existing = model_class.objects.filter(q_objects)
            for obj in existing:
                key = tuple(getattr(obj, field) for field in unique_fields)
                existing_objects[key] = obj
        
        # Identify new objects
        for data in data_list:
            key = tuple(data.get(field) for field in unique_fields)
            if key not in existing_objects:
                new_objects.append(model_class(**data))
        
        # Bulk create new objects
        if new_objects:
            model_class.objects.bulk_create(new_objects)
        
        return len(new_objects), len(existing_objects)
    
    @staticmethod
    def bulk_update_fields(queryset, updates_dict):
        """Bulk update specific fields."""
        try:
            return queryset.update(**updates_dict)
        except Exception as e:
            logger.error(f"Bulk update fields error: {str(e)}")
            return 0
    
    @staticmethod
    def bulk_filter_and_update(model_class, filter_data, update_data):
        """Filter objects and update them in bulk."""
        try:
            queryset = model_class.objects.filter(**filter_data)
            return queryset.update(**update_data)
        except Exception as e:
            logger.error(f"Bulk filter and update error: {str(e)}")
            return 0


class BulkImportExportMixin:
    """Mixin for bulk import/export operations."""
    
    @action(detail=False, methods=['post'])
    def bulk_import(self, request):
        """Import data from uploaded file."""
        if 'file' not in request.FILES:
            return Response(
                {'error': 'No file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        file_obj = request.FILES['file']
        file_format = request.data.get('format', 'json')
        
        try:
            if file_format == 'json':
                import json
                data = json.load(file_obj)
            elif file_format == 'csv':
                import csv
                import io
                
                # Read CSV and convert to list of dicts
                text_file = io.TextIOWrapper(file_obj, encoding='utf-8')
                csv_reader = csv.DictReader(text_file)
                data = list(csv_reader)
            else:
                return Response(
                    {'error': 'Unsupported file format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate data
            validation_result = BulkOperationValidator.validate_bulk_data(data)
            if not validation_result['valid']:
                return Response(validation_result, status=status.HTTP_400_BAD_REQUEST)
            
            # Process import
            serializer = self.get_serializer(data=data, many=True)
            if serializer.is_valid():
                with transaction.atomic():
                    instances = serializer.save()
                    return Response(
                        {
                            'imported_count': len(instances),
                            'message': f'Successfully imported {len(instances)} objects'
                        },
                        status=status.HTTP_201_CREATED
                    )
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Bulk import error: {str(e)}")
            return Response(
                {'error': 'Import failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def bulk_export(self, request):
        """Export data to file."""
        file_format = request.query_params.get('format', 'json')
        
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            
            if file_format == 'json':
                import json
                from django.http import JsonResponse
                
                response = JsonResponse(serializer.data, safe=False)
                response['Content-Disposition'] = 'attachment; filename="export.json"'
                return response
            
            elif file_format == 'csv':
                import csv
                from django.http import HttpResponse
                
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="export.csv"'
                
                if serializer.data:
                    writer = csv.DictWriter(response, fieldnames=serializer.data[0].keys())
                    writer.writeheader()
                    writer.writerows(serializer.data)
                
                return response
            
            else:
                return Response(
                    {'error': 'Unsupported export format'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        except Exception as e:
            logger.error(f"Bulk export error: {str(e)}")
            return Response(
                {'error': 'Export failed'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchProcessor:
    """Process large datasets in batches."""
    
    def __init__(self, batch_size=100):
        self.batch_size = batch_size
    
    def process_in_batches(self, data_list, process_func):
        """Process data in batches."""
        results = []
        errors = []
        
        for i in range(0, len(data_list), self.batch_size):
            batch = data_list[i:i + self.batch_size]
            
            try:
                with transaction.atomic():
                    batch_result = process_func(batch)
                    results.extend(batch_result)
            except Exception as e:
                logger.error(f"Batch processing error: {str(e)}")
                errors.append({
                    'batch_start': i,
                    'batch_end': min(i + self.batch_size, len(data_list)),
                    'error': str(e)
                })
        
        return {
            'results': results,
            'errors': errors,
            'processed_count': len(results),
            'error_count': len(errors)
        }