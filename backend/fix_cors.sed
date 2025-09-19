# Replace the first return Response (active subscription)
/if active_assignment:/,/})/ {
    s/return Response({/response = Response({/
    /})/ a\
            # Add CORS headers for chatbot widget\
            response['Access-Control-Allow-Origin'] = '*'\
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'\
            response['Access-Control-Allow-Headers'] = 'Content-Type, Origin'\
            return response
}
