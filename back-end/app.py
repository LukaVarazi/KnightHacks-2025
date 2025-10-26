import requests
import os
import json
import time 
import re
import io
import base64
from flask import Flask, request, jsonify
from pypdf import PdfReader 
from typing import Tuple, Optional

# --- Configuration ---
# !!! IMPORTANT: You MUST set your actual Gemini API Key here or use environment variables !!!
GEMINI_API_KEY = "AIzaSyDLMUtIu-Bg0qykFwX-6p3-ST5JuWOOEm4" 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
NATIVE_TEXT_THRESHOLD = 50 

app = Flask(__name__)
# Now stores both the extracted text and the optional transcript
extracted_text_store = "No documents analyzed yet."

# Function to handle API requests with exponential backoff
def call_gemini_api(payload, max_retries=5):
    """Handles API request and implements exponential backoff for reliability."""
    # ... (function remains unchanged) ...
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

# --- NEW: M4A Transcription Function ---
def transcribe_audio_bytes(file_bytes: bytes) -> str:
    """Uses Gemini to transcribe an M4A audio file."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key is not configured for audio transcription.")
        
    encoded_audio = base64.b64encode(file_bytes).decode('utf-8')
    
    system_prompt = (
        "You are an expert transcriber. Transcribe the audio precisely. "
        "Do not add any analysis or introductory remarks. "
        "Format the output clearly, including speaker identification if possible."
    )
    
    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {"parts": [
                # Pass audio data with the correct MIME type
                {"inlineData": {"mimeType": "audio/m4a", "data": encoded_audio}},
                {"text": "Transcribe the audio provided."}
            ]}
        ]
    }

    gemini_response = call_gemini_api(payload)
    generated_text = gemini_response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '')
    
    if not generated_text:
        raise Exception("Gemini returned an empty transcription response.")
        
    return generated_text

# --- Refactored PDF Parsing Logic ---
def parse_pdf_bytes(file_bytes: bytes) -> str:
    # ... (function body remains identical to previous version) ...
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
    

# --- Updated Flask Endpoint ---
# Now handles two optional files
@app.route('/upload_data', methods=['POST'])
def upload_data():
    global extracted_text_store
    pdf_file = request.files.get('pdf_file')
    audio_file = request.files.get('audio_file')
    
    if not pdf_file and not audio_file:
        return jsonify({"error": "Missing files: Expecting 'pdf_file' or 'audio_file'."}), 400

    combined_content = []
    source = []

    # Process PDF
    if pdf_file and pdf_file.filename.lower().endswith('.pdf'):
        try:
            pdf_bytes = pdf_file.read()
            pdf_content = parse_pdf_bytes(pdf_bytes)
            combined_content.append(f"--- DOCUMENT ANALYSIS ---\n{pdf_content}")
            source.append("PDF/Image")
        except Exception as e:
            app.logger.error(f"Error during PDF processing: {e}")
            return jsonify({"error": f"Failed to process PDF: {str(e)}"}), 500
    
    # Process M4A
    if audio_file and audio_file.filename.lower().endswith('.m4a'):
        try:
            audio_bytes = audio_file.read()
            audio_transcript = transcribe_audio_bytes(audio_bytes)
            combined_content.append(f"--- CALL TRANSCRIPT ---\n{audio_transcript}")
            source.append("Audio Transcription")
        except Exception as e:
            app.logger.error(f"Error during audio processing: {e}")
            return jsonify({"error": f"Failed to transcribe audio: {str(e)}"}), 500

    # Combine all results into a single string for the agent
    final_content = "\n\n".join(combined_content)
    
    # Store the final parsed string globally
    extracted_text_store = final_content
    
    return jsonify({
        "status": "success",
        "extraction_source": " & ".join(source),
        "message": "Data processing completed successfully.",
        "extracted_content_string": final_content, 
        "character_count": len(final_content),
    }), 200


#======================================================
# LUKA CODE BEYOND THIS POINT - DO NOT TOUCH KURWA!
#======================================================
API_URL = "http://127.0.0.1:8000"
APP_NAME = "agents"
USER_ID = "user1"
SESSION_ID = "s_123"

#======================
# FUNCTIONS (Unchanged from previous version)
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
    elif resp.status_code == 409:
        print("Session already exists.")
    else:
        raise Exception(f"Failed to create session: {resp.status_code} {resp.text}")


def callAgent(prompt: str, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
    """Send prompt to ADK agent and return final string"""
    ensure_session(app_name, user_id, session_id)
    # ... (omitted payload/response logic, identical to previous version) ...
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

def find_data(text):
    """Finds and maps the specific recommendation phrase from the agent's text."""
    mapping = {
        "SUFFICIENT DATA": "SUFFICIENT DATA",
        "MISSING DATA": "INSUFFICIENT DATA",
    }
    pattern = r'RECOMMENDATION:\s*(SUFFICIENT DATA|INSUFFICIENT DATA)'
    match = re.search(pattern, text)
    
    if match:
        return mapping.get(match.group(1), None) 
    return None 

#======================
# RUN AGENT
#======================
if __name__ == "__main__":
    
    # 🛑 CRITICAL: Flask server remains commented out for direct pipeline execution.
    # app.run(host='127.0.0.1', port=5000, debug=True)

    PDF_FILE = "testt.pdf"
    AUDIO_FILE = "first.m4a" # <--- New file to load
    
    combined_content = []

    # 1. Generate the PDF parse string
    try:
        with open(PDF_FILE, 'rb') as f:
            pdf_bytes = f.read()
        
        print(f"--- Attempting to Parse PDF: {PDF_FILE} ---")
        pdf_parse = parse_pdf_bytes(pdf_bytes)
        combined_content.append(f"--- DOCUMENT ANALYSIS ---\n{pdf_parse}")

    except FileNotFoundError:
        print(f"🚨 WARNING: PDF file '{PDF_FILE}' not found. Skipping PDF analysis.")
    except Exception as e:
        print(f"🚨 ERROR during PDF parsing: {e}")
        exit()

    # 2. Generate the M4A transcription string
    try:
        with open(AUDIO_FILE, 'rb') as f:
            audio_bytes = f.read()
            
        print(f"\n--- Attempting to Transcribe Audio: {AUDIO_FILE} ---")
        audio_transcript = transcribe_audio_bytes(audio_bytes)
        combined_content.append(f"--- CALL TRANSCRIPT ---\n{audio_transcript}")
        
    except FileNotFoundError:
        print(f"🚨 WARNING: Audio file '{AUDIO_FILE}' not found. Skipping audio transcription.")
    except Exception as e:
        print(f"🚨 ERROR during audio transcription: {e}")
        # Decide if you want to exit here or continue with just the PDF text

    # Final combined text
    if not combined_content:
        print("🚨 ERROR: No data (PDF or Audio) was successfully loaded. Exiting.")
        exit()

    initialParse = "\n\n".join(combined_content)
    
    print("\n--- Combined Text Preview ---")
    print(initialParse[:200] + "..." if len(initialParse) > 200 else initialParse)

    # 3. AGENT PIPELINE Execution (Unchanged)
    print("\n--- Starting Agent Pipeline ---")

    # STEP 1: Check and Sort Data
    parsedText = initialParse + "\n\nAction: Sort_Initial"
    print(f"\nCalling Agent with Action: Sort_Initial...")
    sortInitialResult = callAgent(parsedText)
    print("--- Agent Response (Sort_Initial) ---")
    print(sortInitialResult)

    recommendation = find_recommendation(sortInitialResult)
    print(f"\nExtracted Recommendation: {recommendation}")

    sortResult = ""
    if recommendation == "ACCEPT":
        # STEP 2: Ensure No Files are Missing
        print("\nRunning ACCEPT path...")
        parsedText = initialParse + "\n\nAction: Sort"
        sortResult = callAgent(parsedText)
    else:
        print("\nRunning REJECT/INSUFFICIENT path...")
        parsedText = initialParse + "\n\nAction: Email"
        sortResult = callAgent(parsedText)

    dataSufficiency = find_data(sortResult)
    print(f"\nExtracted Data Sufficiency: {dataSufficiency}")

    sort2Result = ""
    if dataSufficiency == "SUFFICIENT DATA":
        # STEP 3:
        print("\nRunning SUFFICIENT path...")
        parsedText = initialParse + "\n\nAction: Wranggler2"
        sort2Result = callAgent(parsedText)
    else:
        print("\nRunning REJECT/INSUFFICIENT path...")
        parsedText = initialParse + "\n\nAction: Email"
        sort2Result = callAgent(parsedText)

    # STEP 4:
    combinedData = initialParse + "\n\n" + sortResult + "\n\n" + sort2Result
    parsedText = combinedData + "\n\nAction: Wranggler3"
    sort3Result = callAgent(parsedText)

    final_result = sort3Result

    
    print("\n--- Final Agent Response (Step 4 Action) ---")
    print(final_result)
    print("\n--- Pipeline Complete ---")