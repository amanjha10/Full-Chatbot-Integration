"""
Common response utilities to standardize API responses across the project.
"""
from rest_framework import status
from rest_framework.response import Response


def success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    """
    Standard success response format.
    
    Args:
        data: Response data
        message: Success message
        status_code: HTTP status code
    
    Returns:
        Response object
    """
    response_data = {}
    
    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data['data'] = data
    
    if message:
        response_data['message'] = message
    
    return Response(response_data, status=status_code)


def error_response(error_message, status_code=status.HTTP_400_BAD_REQUEST, details=None):
    """
    Standard error response format.
    
    Args:
        error_message: Error message
        status_code: HTTP status code
        details: Additional error details
    
    Returns:
        Response object
    """
    response_data = {'error': error_message}
    
    if details:
        response_data['details'] = details
    
    return Response(response_data, status=status_code)


def validation_error_response(errors, message="Validation failed"):
    """
    Standard validation error response format.
    
    Args:
        errors: Validation errors (usually from serializer.errors)
        message: Error message
    
    Returns:
        Response object
    """
    return Response({
        'error': message,
        'validation_errors': errors
    }, status=status.HTTP_400_BAD_REQUEST)


def not_found_response(resource_name="Resource"):
    """
    Standard 404 not found response.
    
    Args:
        resource_name: Name of the resource that was not found
    
    Returns:
        Response object
    """
    return Response({
        'error': f'{resource_name} not found'
    }, status=status.HTTP_404_NOT_FOUND)


def forbidden_response(message="Access denied"):
    """
    Standard 403 forbidden response.
    
    Args:
        message: Forbidden message
    
    Returns:
        Response object
    """
    return Response({
        'error': message
    }, status=status.HTTP_403_FORBIDDEN)


def unauthorized_response(message="Authentication required"):
    """
    Standard 401 unauthorized response.
    
    Args:
        message: Unauthorized message
    
    Returns:
        Response object
    """
    return Response({
        'error': message
    }, status=status.HTTP_401_UNAUTHORIZED)


def server_error_response(message="Internal server error", details=None):
    """
    Standard 500 server error response.
    
    Args:
        message: Error message
        details: Additional error details
    
    Returns:
        Response object
    """
    response_data = {'error': message}
    
    if details:
        response_data['details'] = str(details)
    
    return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
