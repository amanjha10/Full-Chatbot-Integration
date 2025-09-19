# Read the file
with open('chatbot/views.py', 'r') as f:
    lines = f.readlines()

# Find the function and add CORS headers
in_function = False
modified_lines = []
i = 0

while i < len(lines):
    line = lines[i]
    
    # Check if we're in the company_subscription_status_view function
    if 'def company_subscription_status_view' in line:
        in_function = True
        modified_lines.append(line)
    elif in_function and line.strip().startswith('return Response({'):
        # Replace return Response with response = Response
        new_line = line.replace('return Response({', 'response = Response({')
        modified_lines.append(new_line)
        
        # Find the closing }) and add CORS headers after it
        j = i + 1
        while j < len(lines) and '})' not in lines[j]:
            modified_lines.append(lines[j])
            j += 1
        
        # Add the closing line
        if j < len(lines):
            modified_lines.append(lines[j])
            
        # Add CORS headers
        modified_lines.append('            # Add CORS headers for chatbot widget\n')
        modified_lines.append("            response['Access-Control-Allow-Origin'] = '*'\n")
        modified_lines.append("            response['Access-Control-Allow-Methods'] = 'GET, OPTIONS'\n")
        modified_lines.append("            response['Access-Control-Allow-Headers'] = 'Content-Type, Origin'\n")
        modified_lines.append('            return response\n')
        
        i = j + 1
        continue
    elif in_function and (line.strip().startswith('def ') and 'company_subscription_status_view' not in line):
        # We've reached the next function, stop processing
        in_function = False
        modified_lines.append(line)
    else:
        modified_lines.append(line)
    
    i += 1

# Write back to file
with open('chatbot/views.py', 'w') as f:
    f.writelines(modified_lines)

print("✅ CORS headers added to all return statements in company_subscription_status_view")
