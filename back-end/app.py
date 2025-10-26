import requests
import os
import json
import time 
import re
import io
import base64
from threading import Thread # Required for running Flask in background (optional, but good practice)
from flask import Flask, request, jsonify
from pypdf import PdfReader 

# --- Configuration ---
GEMINI_API_KEY = "AIzaSyDLMUtIu-Bg0qykFwX-6p3-ST5JuWOOEm4" 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
NATIVE_TEXT_THRESHOLD = 50 

app = Flask(__name__)
extracted_text_store = "No documents analyzed yet."

# Function to handle API requests with exponential backoff
def call_gemini_api(payload, max_retries=5):
    """Handles API request and implements exponential backoff for reliability."""
    for attempt in range(max_retries):
        try:
            headers = {'Content-Type': 'application/json'}
            response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", 
                                     headers=headers, 
                                     data=json.dumps(payload),
                                     timeout=120)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise e
    return None

# --- Core Parsing Logic Extracted into a Function ---
def parse_pdf_bytes(file_bytes):
    """
    Core logic to parse PDF bytes, falling back to Gemini for OCR.
    Returns the extracted string or raises an exception on failure.
    """
    native_text = ""
    source = "Unknown"

    # 1. Attempt Native Text Extraction
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            native_text += page.extract_text() or ""
        native_text = ' '.join(native_text.split())
    except Exception as e:
        app.logger.warning(f"pypdf native extraction failed: {e}")
        pass
    
    # 2. Hybrid Check and Fallback to Gemini
    if len(native_text) > NATIVE_TEXT_THRESHOLD:
        extracted_content = native_text
        source = "Native Extraction (pypdf)"
    else:
        if not GEMINI_API_KEY:
            raise ValueError("Gemini API Key is not configured for OCR/Image Analysis fallback.")
        
        # Use Gemini for OCR/Image Analysis
        encoded_pdf = base64.b64encode(file_bytes).decode('utf-8')

        system_prompt = (
            "You are an expert document analyst specializing in accident reports. "
            "Extract all text content from the document, including any text visible within images (OCR). "
            "Crucially, for any embedded images depicting car crashes, provide a detailed, objective description "
            "of the visible damage, position of vehicles, and environment. Combine the extracted text and "
            "image descriptions into a single, cohesive narrative. Do not include any introductory or concluding remarks."
        )
        
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {"parts": [
                    {"inlineData": {"mimeType": "application/pdf", "data": encoded_pdf}},
                    {"text": "Analyze the document and provide the combined narrative as requested."}
                ]}
            ]
        }
        
        gemini_response = call_gemini_api(payload)
        generated_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
        
        if not generated_text:
            raise Exception("Gemini returned an empty text response.")

        extracted_content = generated_text
        source = "Gemini OCR/Image Analysis Fallback"

    print(f"Extraction Source: {source}")
    return extracted_content

# --- Flask Endpoints (Mostly Unchanged) ---
@app.route('/', methods=['GET'])
def index():
    """Serves a basic API status message."""
    return jsonify({
        "status": "API is operational (Hybrid PDF/Image Analyzer)",
        "message": "Send a POST request to /upload_pdf with a file named 'pdf_file' to begin analysis.",
        "last_text_preview": extracted_text_store[:80] + "..." if len(extracted_text_store) > 80 else extracted_text_store
    }), 200

@app.route('/upload_pdf', methods=['POST'])
def upload_pdf():
    global extracted_text_store

    if 'pdf_file' not in request.files:
        return jsonify({"error": "Missing file: Expecting a file named 'pdf_file' in the form data."}), 400
    
    file = request.files['pdf_file']
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

    file_bytes = file.read()
    
    try:
        extracted_content = parse_pdf_bytes(file_bytes)
        source = "Gemini/pypdf" # Simplified source for the API response after refactoring
    except Exception as e:
        app.logger.error(f"Error during PDF processing: {e}")
        return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500

    # Store the final parsed string globally
    extracted_text_store = extracted_content
    
    return jsonify({
        "status": "success",
        "extraction_source": source,
        "message": f"Text and image analysis completed successfully via {source}.",
        "extracted_content_string": extracted_content, 
        "character_count": len(extracted_content),
    }), 200



#======================================================
# LUKA CODE BEYOND THIS POINT - DO NOT TOUCH KURWA!
#======================================================
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
    """Finds and maps the specific recommendation phrase from the agent's text."""
    mapping = {
        "ACCEPT DATA": "ACCEPT",
        "REJECT DATA": "REJECT",
        "INCOMPLETE DATA": "INSUFFICIENT DATA"
    }

    pattern = r'RECOMMENDATION:\s*(ACCEPT DATA|REJECT DATA|INCOMPLETE DATA)'
    match = re.search(pattern, text)
    
    if match:
        return mapping.get(match.group(1), None) 
    return None 

#======================
# RUN AGENT
#======================
if __name__ == "__main__":
    # NOTE: You MUST have a file named 'test_document.pdf' in the same directory
    # for this test to succeed.
    TEST_FILE_PATH = "testt.pdf"
    
    # We will run the parsing logic directly to get the required string.
    try:
        with open(TEST_FILE_PATH, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"--- Attempting to Parse PDF: {TEST_FILE_PATH} ---")
        initialParse = parse_pdf_bytes(pdf_bytes)
        
        print("\n--- Parsed Text Preview ---")
        print(initialParse[:200] + "..." if len(initialParse) > 200 else initialParse)

    except FileNotFoundError:
        print(f"🚨 ERROR: Test file '{TEST_FILE_PATH}' not found.")
        print("Please create a PDF file with that name to run the agent pipeline.")
        exit()
    except Exception as e:
        print(f"🚨 ERROR during PDF parsing: {e}")
        exit()
    
    #======================
    # AGENT PIPELINE
    #======================

    print("\n--- Starting Agent Pipeline ---")

    # STEP 1: Check and Sort Data
    parsedText = initialParse + "\n\nAction: Sort_Initial"
    print(f"\nCalling Agent with Action: Sort_Initial...")
    result = callAgent(parsedText)
    print("--- Agent Response (Sort_Initial) ---")
    print(result)

    recommendation = find_recommendation(result)
    print(f"\nExtracted Recommendation: {recommendation}")

    final_result = ""
    if recommendation == "ACCEPT":
        # STEP 2: Ensure No Files are Missing
        print("\nRunning ACCEPT path...")
        parsedText = initialParse + "\n\nAction: Sort"
        final_result = callAgent(parsedText)
    else:
        print("\nRunning REJECT/INSUFFICIENT path...")
        parsedText = initialParse + "\n\nAction: Email"
        final_result = callAgent(parsedText)

    print("\n--- Final Agent Response (Step 2 Action) ---")
    print(final_result)
    print("\n--- Pipeline Complete ---")

    # Optional: Run Flask server in a separate thread if needed for API testing later
    # Thread(target=lambda: app.run(host='127.0.0.1', port=5000)).start()