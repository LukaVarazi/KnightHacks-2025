import requests
import os
import json
import time # Added for wait time in case of connection issues

# --- Prerequisites ---
# 1. Ensure your Flask app (app.py) is running in a separate terminal via 'python app.py'.
# 2. Ensure you have the requests library installed: pip install requests
# 3. Create a small PDF file named 'test_document.pdf' in the same directory for testing.

def test_pdf_upload():
    """
    Tests the PDF upload endpoint (/upload_pdf) of the Flask application,
    which now calls the Gemini API for summarization.
    """
    # The URL matches the running Flask server and the POST route
    url = 'http://127.0.0.1:5000/upload_pdf'
    pdf_filename = 'pdftest.pdf'

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
    # 4. Validate the response structure for the new Gemini-based API
    if response.status_code == 200 and data.get('status') == 'success' and 'summary' in data:
        print(f"SUCCESS: The PDF upload and Gemini summarization worked!")
        print(f"Summary Length: {data.get('summary_length')} words.")
        print(f"Summary Preview: {data.get('summary')[:100]}...")
    else:
        print("FAILURE: The API returned an error or the expected JSON structure was missing.")
        if 'error' in data:
             print(f"Server Error Message: {data['error']}")


if __name__ == '__main__':
    test_pdf_upload()
