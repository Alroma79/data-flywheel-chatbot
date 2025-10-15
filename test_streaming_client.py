import requests
import json
import traceback

def test_streaming():
    url = "http://localhost:8000/api/v1/chat"

    payload = {
        "message": "Generate a streaming response",
        "stream": True
    }
    # Print payload to verify
    print(f"Payload: {payload}")
    print(f"Payload type: {type(payload)}")
    print(f"Payload stream type: {type(payload.get('stream'))}")

    headers = {
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, json=payload, headers=headers, stream=True)

        print("Response Status Code:", response.status_code)
        print("Response Headers:", dict(response.headers))
        print("Response Content Type:", response.headers.get('Content-Type', 'No content type'))

        if response.status_code == 200:
            print("Streaming Started:")
            # Read entire response content for debugging
            content = response.content.decode('utf-8')
            print("Full Response Content:")
            print(content)

            # Try parsing lines
            for line in content.split('\n\n'):
                if line.startswith('data: '):
                    try:
                        data = json.loads(line[6:])
                        print("Parsed Data:")
                        print(json.dumps(data, indent=2))
                    except Exception as e:
                        print(f"Error parsing line: {e}")
                        print("Problematic Line:", line)
        else:
            print("Error Status Code:", response.status_code)
            print("Error Response Text:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_streaming()