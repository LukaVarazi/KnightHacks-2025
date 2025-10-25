import requests
import requests
import os
import json
import time 
import re

# --- Prerequisites ---
# 1. Ensure your Flask app (app.py) is running in a separate terminal via 'python app.py'.
# 2. Ensure you have the requests and pypdf libraries installed: pip install requests pypdf
# 3. Create a small PDF file named 'test_document.pdf' in the same directory for testing.

def test_pdf_upload():
    """
    Tests the PDF upload endpoint (/upload_pdf) of the Flask application,
    which now uses a hybrid approach (pypdf + Gemini OCR/Image Analysis fallback).
    """
    # The URL matches the running Flask server and the POST route
    url = 'http://127.0.0.1:5000/upload_pdf'
    pdf_filename = 'testt.pdf'

    print(f"Attempting to connect to: {url}")
    
    # 1. Check if the test file exists
    if not os.path.exists(pdf_filename):
        print("-" * 60)
        print(f"ERROR: Test file '{pdf_filename}' not found.")
        print("ACTION: Please create a small PDF file with some text and name it 'test_document.pdf' in this folder.")
        print("-" * 60)
        return

    # 2. Define the files payload and send request
    try:
        with open(pdf_filename, 'rb') as f:
            # The dictionary key must match the expected input name in app.py ('pdf_file')
            files = {'pdf_file': (pdf_filename, f, 'application/pdf')}
            
            # Make the POST request
            print("Sending request to Flask server...")
            start_time = time.time()
            response = requests.post(url, files=files)
            end_time = time.time()

        # 3. Process the response
        print("-" * 60)
        print(f"Request Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")
        
        try:
            # Attempt to parse the JSON response
            data = response.json()
            print("Response JSON:")
            print(json.dumps(data, indent=4))
        except requests.exceptions.JSONDecodeError:
            # Handle cases where the server returns an unexpected non-JSON response
            print("Response content is not valid JSON (check server logs for errors):")
            print(response.text)
            data = {} # Ensure 'data' is defined for the check below

    except requests.exceptions.ConnectionError:
        print("-" * 60)
        print("CRITICAL ERROR: Could not connect to the Flask server.")
        print("ACTION: Please ensure 'app.py' is running via 'python app.py' in a separate terminal.")
        print("-" * 60)
        return
    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")
        return
    
    print("-" * 60)
    # 4. Validate the response structure for the new Hybrid API
    if response.status_code == 200 and data.get('status') == 'success' and 'extracted_text' in data:
        source = data.get('extraction_source', 'Unknown')
        # Updated success message to reflect the new multimodal capability
        print(f"SUCCESS: Hybrid document analysis complete (Text + Image Analysis)! Source: {source}")
        print(f"Character Count: {data.get('character_count')} characters.")
        print(f"Text Preview: {data.get('extracted_text')[:100]}...")
    else:
        print("FAILURE: The API returned an error or the expected JSON structure was missing.")
        if 'error' in data:
             print(f"Server Error Message: {data['error']}")







API_URL = "http://127.0.0.1:8000"
APP_NAME = "agents"
USER_ID = "user1"
SESSION_ID = "s_123"

#======================
# FUNCTIONS
#======================
def ensure_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
    """Create session if it doesn't exist"""
    session_payload = {"state": {}}
    resp = requests.post(
        f"{API_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
        json=session_payload
    )
    if resp.status_code in (200, 201):
        print("Session ready.")
    elif resp.status_code == 409:  # Session already exists
        print("Session already exists.")
    else:
        raise Exception(f"Failed to create session: {resp.status_code} {resp.text}")


def callAgent(prompt: str, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
    """Send prompt to ADK agent and return final string"""
    # Ensure session exists
    ensure_session(app_name, user_id, session_id)

    payload = {
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {
            "role": "user",
            "parts": [{"text": prompt}]
        }
    }

    response = requests.post(f"{API_URL}/run", json=payload)

    if response.status_code == 200:
        data = response.json()
        # ADK returns a list of events; last event usually has the final text
        for event in reversed(data):
            content = event.get("content", {})
            parts = content.get("parts", [])
            for part in parts:
                if "text" in part:
                    return part["text"].strip()
        return "No text found in agent response."
    else:
        return f"Error {response.status_code}: {response.text}"

def find_recommendation(text):
    # Map the full phrases to your desired output
    mapping = {
        "ACCEPT DATA": "ACCEPT",
        "REJECT DATA": "REJECT",
        "INCOMPLETE DATA": "INSUFFICIENT DATA"
    }

    # Regex to find the recommendation
    pattern = r'RECOMMENDATION:\s*(ACCEPT DATA|REJECT DATA|INSUFFICIENT DATA)'
    match = re.search(pattern, text)
    
    if match:
        return mapping[match.group(1)]
    return None  # No recommendation found

#======================
# AGENT PIPELINE
#======================
initialParse = """
The client was involved in a rear-end car accident on August 12, 2024, at 3:45 PM near NW 36th Street and LeJeune Road in Miami, FL. 
He was taken by ambulance to Jackson Memorial Hospital. The police report indicates the other driver was at fault. 
Total insurance payout from his car policy (Geico) is $50,000, and medical bills amount to $10,000. 
Injuries include whiplash and shoulder strain confirmed by MRI. He was treated within 24 hours. 
Defendant: John Doe, 305-555-8822, driver of vehicle B.
"""



#======================
# RUN AGENT
#======================
if __name__ == "__main__":
    #initialParse = test_pdf_upload()

    #======================
    # AGENT PIPELINE
    #======================

    # STEP 1: Check and Sort Data
    parsedText = initialParse + "\n\nAction: Sort_Initial"
    result = callAgent(parsedText)
    recommendation = find_recommendation(result)

    if recommendation == "ACCEPT":
        # STEP 2: Ensure No Files are Missing
        parsedText = initialParse + "\n\nAction: Sort"
        result = callAgent(parsedText)
    else:
        parsedText = initialParse + "\n\nAction: Email"
        result = callAgent(parsedText)

    print(result)














