import requests
import os
import json
import time

# --- Configuration ---
# NOTE: The Flask server MUST be running in a separate terminal on this port.
FLASK_URL = 'http://127.0.0.1:5000/upload_pdf'
PDF_FILENAME = 'testt.pdf' # IMPORTANT: Create a PDF with this name in this directory.

def run_test():
    """
    Sends a test PDF file to the Flask server's analysis endpoint.
    """
    print(f"--- Starting Hybrid Analysis Test ---")

    # 1. Check if the test file exists
    if not os.path.exists(PDF_FILENAME):
        print("\n" + "=" * 60)
        print(f" CRITICAL ERROR: Test file '{PDF_FILENAME}' not found.")
        print(" ACTION: Please create a PDF file (ideally one with an image of a crash) and name it 'test_document.pdf' in this folder.")
        print("=" * 60 + "\n")
        return

    # 2. Define the files payload and send request
    try:
        with open(PDF_FILENAME, 'rb') as f:
            # The dictionary key 'pdf_file' MUST match the name expected by app.py
            files = {'pdf_file': (PDF_FILENAME, f, 'application/pdf')}

            print(f"Sending request to Flask server at {FLASK_URL}...")
            start_time = time.time()
            response = requests.post(FLASK_URL, files=files)
            end_time = time.time()

        # 3. Process the response
        print("-" * 60)
        print(f"Request Status Code: {response.status_code}")
        print(f"Response Time: {end_time - start_time:.2f} seconds")

        try:
            data = response.json()
            
            # 4. Validate the response
            if response.status_code == 200 and data.get('status') == 'success':
                source = data.get('extraction_source', 'Unknown')
                text_output = data.get('extracted_content_string', '')
                char_count = data.get('character_count', 0)

                print("\n" + "=" * 60)
                print(f"SUCCESS: Analysis Completed!")
                print(f"Source Method: {source}")
                print(f"Character Count: {char_count}")
                print("=" * 60)
                print("Extracted/Analyzed Content:")
                print(text_output)
                print("=" * 60)

            else:
                print("FAILURE: The API returned an error or unexpected JSON.")
                print("Server Response:")
                print(json.dumps(data, indent=4))

        except requests.exceptions.JSONDecodeError:
            print("ERROR: Server response was not valid JSON. Check app.py console for errors.")
            print(response.text)

    except requests.exceptions.ConnectionError:
        print("\n" + "=" * 60)
        print("CRITICAL ERROR: Could not connect to the Flask server (port 5000).")
        print("ACTION: Ensure 'app.py' is running via 'python app.py' in a separate terminal.")
        print("=" * 60 + "\n")
    except Exception as e:
        print(f"An unexpected error occurred during the test: {e}")

if __name__ == '__main__':
    run_test()