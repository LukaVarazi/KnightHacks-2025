import io
import os
import json
import base64
import requests
import time
from flask import Flask, request, jsonify
from pypdf import PdfReader # Used for fast, accurate native text extraction

# --- Configuration ---
# !!! IMPORTANT: You MUST set your actual Gemini API Key here or use environment variables !!!
GEMINI_API_KEY = "AIzaSyDLMUtIu-Bg0qykFwX-6p3-ST5JuWOOEm4" 
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent"
# If native text is less than this threshold, we assume it's a scanned/image-based PDF and use Gemini.
NATIVE_TEXT_THRESHOLD = 50 

app = Flask(__name__)
# Global variable for a basic server status check and storing the final parsed string
extracted_text_store = "No documents analyzed yet."

# Function to handle API requests with exponential backoff
def call_gemini_api(payload, max_retries=5):
    """Handles API request and implements exponential backoff for reliability."""
    for attempt in range(max_retries):
        try:
            headers = {'Content-Type': 'application/json'}
            # API Key is appended to the URL as a query parameter
            response = requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}", 
                                     headers=headers, 
                                     data=json.dumps(payload),
                                     timeout=120) # Added timeout
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            # Retry on rate limiting (429) or common server errors (5xx)
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                wait_time = 2 ** attempt
                time.sleep(wait_time)
            else:
                raise e
    return None

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
    native_text = ""
    source = "Unknown"

    # --- Step 1: Attempt Native Text Extraction (Accuracy Priority) ---
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            native_text += page.extract_text() or ""
        # Clean up excessive whitespace/newlines
        native_text = ' '.join(native_text.split())
    except Exception:
        # If pypdf fails (e.g., corrupted file), we ignore the error and proceed to Gemini fallback
        pass
    
    # --- Step 2: Hybrid Check and Fallback to Gemini (OCR/Image Analysis) ---
    if len(native_text) > NATIVE_TEXT_THRESHOLD:
        # Success: Native text is sufficient (Text-only PDF)
        extracted_content = native_text
        source = "Native Extraction (pypdf)"
    else:
        # Fallback: Text is image-based or sparse, use Gemini for OCR and visual description
        if not GEMINI_API_KEY:
            return jsonify({"error": "Gemini API Key is not configured for OCR/Image Analysis fallback."}), 500
        
        try:
            # Encode PDF bytes to base64 for API transmission
            encoded_pdf = base64.b64encode(file_bytes).decode('utf-8')

            # CRITICAL: Prompt for combined text extraction AND detailed image description
            system_prompt = (
                "You are an expert document analyst specializing in accident reports. "
                "Extract all text content from the document, including any text visible within images (OCR). "
                "Crucially, for any embedded images depicting car crashes, provide a detailed, objective description "
                "of the visible damage, position of vehicles, and environment. Combine the extracted text and "
                "image descriptions into a single, cohesive narrative. Do not include any introductory or concluding remarks."
            )
            
            payload = {
                # Place system instruction here for better control
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
            
        except Exception as e:
            app.logger.error(f"Error during Gemini fallback: {e}")
            return jsonify({"error": f"Failed to perform Gemini OCR/Image Analysis: {str(e)}"}), 500

    # --- Step 3: Return Response ---
    # Store the final parsed string globally
    extracted_text_store = extracted_content
    
    return jsonify({
        "status": "success",
        "extraction_source": source,
        "message": f"Text and image analysis completed successfully via {source}.",
        "extracted_content_string": extracted_content, # The final string containing text and image descriptions
        "character_count": len(extracted_content),
    }), 200

if __name__ == '__main__':
    # Flask must be run in a separate, dedicated terminal
    app.run(host='127.0.0.1', port=5000, debug=True)