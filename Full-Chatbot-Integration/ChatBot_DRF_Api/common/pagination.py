"""
Common pagination utilities to eliminate duplicate pagination code across the project.
"""
from rest_framework import status
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.core.paginator import Paginator


class StandardPagination(PageNumberPagination):
    """
    Standard pagination class for consistent pagination across all apps.
    Consolidates duplicate pagination logic from authentication/views.py
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'page_size': len(data),  # Actual number of items on this page
            'requested_page_size': self.get_page_size(self.request),  # What was requested
            'results': data
        })


def paginate_queryset(queryset, request, serializer_class, page_size=10):
    """
    Generic pagination function to eliminate duplicate pagination patterns.
    
    Args:
        queryset: Django QuerySet to paginate
        request: Django request object
        serializer_class: Serializer class to use for data serialization
        page_size: Items per page (default: 10)
    
    Returns:
        Response object with paginated data
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', page_size)), 100)
        
        paginator = Paginator(queryset, page_size)
        try:
            page_obj = paginator.page(page)
        except:
            page_obj = paginator.page(1)
        
        serializer = serializer_class(page_obj, many=True)
        
        return Response({
            'count': paginator.count,
            'current_page': page_obj.number,
            'total_pages': paginator.num_pages,
            'has_next': page_obj.has_next(),
            'has_previous': page_obj.has_previous(),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Pagination failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def paginate_with_drf(queryset, request, serializer_class):
    """
    DRF-style pagination using StandardPagination class.
    
    Args:
        queryset: Django QuerySet to paginate
        request: Django request object
        serializer_class: Serializer class to use for data serialization
    
    Returns:
        Response object with paginated data or fallback response
    """
    try:
        paginator = StandardPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        if page is not None:
            serializer = serializer_class(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        # Fallback if pagination fails
        serializer = serializer_class(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': f'Pagination failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def get_pagination_params(request, default_page_size=10):
    """
    Extract and validate pagination parameters from request.
    
    Args:
        request: Django request object
        default_page_size: Default page size if not specified
    
    Returns:
        tuple: (page, page_size) with validated values
    """
    try:
        page = int(request.GET.get('page', 1))
        page_size = min(int(request.GET.get('page_size', default_page_size)), 100)
        return page, page_size
    except (ValueError, TypeError):
        return 1, default_page_size


def create_paginated_response(paginator, page_obj, serialized_data, extra_data=None):
    """
    Create a standardized paginated response.
    
    Args:
        paginator: Django Paginator instance
        page_obj: Django Page instance
        serialized_data: Serialized data for the page
        extra_data: Optional extra data to include in response
    
    Returns:
        dict: Standardized pagination response
    """
    response_data = {
        'count': paginator.count,
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
        'results': serialized_data
    }
    
    if extra_data:
        response_data.update(extra_data)
    
    return response_data
