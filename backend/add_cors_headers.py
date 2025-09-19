import re

# Read the file
with open('chatbot/views.py', 'r') as f:
    content = f.read()

# Pattern to find return Response statements in company_subscription_status_view
pattern = r'(def company_subscription_status_view.*?)(return Response\(\{[^}]+\}\))'

def add_cors_to_response(match):
    func_content = match.group(1)
    return_statement = match.group(2)
    
    # Replace return Response with response = Response and add CORS headers
    new_return = return_statement.replace('return Response(', 'response = Response(')
    cors_headers = '''
            # Add CORS headers for chatbot widget
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Origin'
            return response'''
    
    return func_content + new_return + cors_headers

# Apply the replacement
content = re.sub(pattern, add_cors_to_response, content, flags=re.DOTALL)

# Write back to file
with open('chatbot/views.py', 'w') as f:
    f.write(content)

print("✅ CORS headers added to company_subscription_status_view")
