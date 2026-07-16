from rest_framework.views import exception_handler


def api_exception_handler(exc, context):
    """Normalize DRF's {'detail': ...} to our {'error': ...} so API
    clients only ever parse one error shape. Field-validation errors
    keep their own {'errors': {field: [...]}} shape - different animal."""
    response = exception_handler(exc, context)
    if response is not None and isinstance(response.data, dict) and 'detail' in response.data:
        response.data = {'error': str(response.data['detail'])}
    return response
