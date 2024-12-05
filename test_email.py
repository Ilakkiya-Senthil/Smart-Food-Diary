import json

# Your API response (Python dictionary)
api_response = {
    'analysis_id': '1c868a1b-e59d-4041-bb59-7fa0051ba9bb',
    'scopes': ['nutrition:macro', 'nutrition:micro'],
    'items': [
        {
            'position': {'x': 0.33, 'y': 0.0263, 'width': 0.5019, 'height': 0.8902},
            'food': [{'confidence': 1.0, 'quantity': 211.0}]
        }
    ]
}

# Convert it to a JSON string with double quotes
json_response = json.dumps(api_response, indent=4)

print(json_response)
