from logging.config import fileConfig
import requests
import os
import json
import time
import re
import io
import base64
import glob
from flask import Flask, request, jsonify
from pypdf import PdfReader
from typing import Tuple, Optional, List, Dict, Any
import sys
from flask_cors import CORS

from util import nuke_files, save_files

from dotenv import load_dotenv

# --- Configuration & Globals ---
# NOTE: Using a placeholder API key. Replace with your actual key.
GEMINI_API_KEY = os.environ.get(
    "GEMINI_API_KEY",
)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
NATIVE_TEXT_THRESHOLD = 50

# Agent Development Kit (ADK) Configuration
API_URL = "http://127.0.0.1:8000"  # ADK Server URL

# CRITICAL FIX: APP_NAME must match the root agent's name defined in agent.py
# The root agent name is 'agent_coordinator'.
APP_NAME = "agent_coordinator"

USER_ID = "progressive_user_1"
SESSION_ID = "s_progressive_claim_1"
DATA_FOLDER = "./media"

# Global store for the final string result (stores all step results)
# The frontend can fetch this after the full pipeline runs.
pipeline_result_store: List[Dict[str, str]] = []

app = Flask(__name__)
CORS(app)  # gets rid of dumb reasonable security

file_context = ""

# --- Utility Functions (Keep as-is for robust file processing) ---


def delimit_output_string(output_text: str) -> str:
    """
    Separates values by placing a 'thinking face' emoji (🤔) next to a simplified
    set of keywords and patterns for frontend delimiting.
    """
    return output_text

    DELIMITER_EMOJI = " 🤔"

    # 1. 'approved' (Case-insensitive)
    output_text = re.sub(
        r"(approved)", r"\1" + DELIMITER_EMOJI, output_text, flags=re.IGNORECASE
    )

    # 2. 'denied' (Case-insensitive)
    output_text = re.sub(
        r"(denied)", r"\1" + DELIMITER_EMOJI, output_text, flags=re.IGNORECASE
    )

    # 3. 'Pros' (using word boundary \b)
    output_text = re.sub(r"\b(Pros)\b", r"\1" + DELIMITER_EMOJI, output_text)

    # 4. 'Cons' (using word boundary \b)
    output_text = re.sub(r"\b(Cons)\b", r"\1" + DELIMITER_EMOJI, output_text)

    # 5. The 2-digit number followed by a '%' sign (e.g., "85%")
    output_text = re.sub(r"(\d{2}%)", r"\1" + DELIMITER_EMOJI, output_text)

    # 6. Insurance payout labels
    output_text = re.sub(
        r"Insurance payout:", r"Insurance payout:" + DELIMITER_EMOJI, output_text
    )
    output_text = re.sub(
        r"Attorney fee \(33⅓%\):",
        r"Attorney fee (33⅓%):" + DELIMITER_EMOJI,
        output_text,
    )
    output_text = re.sub(
        r"Medical fees:", r"Medical fees:" + DELIMITER_EMOJI, output_text
    )
    output_text = re.sub(
        r"Client remaining:", r"Client remaining:" + DELIMITER_EMOJI, output_text
    )

    return output_text


def call_gemini_api(payload, max_retries=5):
    """Handles API request and implements exponential backoff."""
    for attempt in range(max_retries):
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers=headers,
                data=json.dumps(payload),
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)
            else:
                raise e
    return None


def call_simple_gemini_api(payload, max_retries=5):
    """Handles API request and implements exponential backoff."""
    for attempt in range(max_retries):
        try:
            headers = {"Content-Type": "application/json"}
            response = requests.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}",
                headers=headers,
                data=json.dumps(payload),
                timeout=120,
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if response.status_code in [429, 500, 503] and attempt < max_retries - 1:
                wait_time = 2**attempt
                time.sleep(wait_time)
            else:
                raise e

    return None


def call_gemini(payload):
    gemini_response = call_simple_gemini_api(payload)
    generated_text = (
        gemini_response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    return generated_text


def transcribe_audio_bytes(file_bytes: bytes) -> str:
    """Uses Gemini to transcribe an M4A audio file."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key is not configured.")

    encoded_audio = base64.b64encode(file_bytes).decode("utf-8")
    system_prompt = "You are an expert transcriber. Transcribe the audio precisely. Do not add any analysis or introductory remarks. Format the output clearly, including speaker identification if possible."

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {
                "parts": [
                    {"inlineData": {"mimeType": "audio/m4a", "data": encoded_audio}},
                    {"text": "Transcribe the audio provided."},
                ]
            }
        ],
    }

    gemini_response = call_gemini_api(payload)
    generated_text = (
        gemini_response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    if not generated_text:
        raise Exception("Gemini returned an empty transcription response.")

    return generated_text


def analyze_image_bytes(file_bytes: bytes, mime_type: str) -> str:
    """Uses Gemini to analyze image bytes (PNG/JPG) for text and description."""
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key is not configured for image analysis.")

    encoded_image = base64.b64encode(file_bytes).decode("utf-8")

    system_prompt = (
        "You are an expert document analyst specializing in accident reports. "
        "Extract all text content from the image (OCR). "
        "Crucially, provide a detailed, objective description of the visual content, "
        "such as visible damage, position of vehicles, and environment. "
        "Combine the extracted text and visual descriptions into a single, cohesive narrative. "
        "Do not include any introductory or concluding remarks."
    )

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {
                "parts": [
                    {"inlineData": {"mimeType": mime_type, "data": encoded_image}},
                    {
                        "text": "Analyze the image and provide the combined narrative as requested."
                    },
                ]
            }
        ],
    }

    gemini_response = call_gemini_api(payload)
    generated_text = (
        gemini_response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    if not generated_text:
        raise Exception("Gemini returned an empty text response during image analysis.")

    return generated_text


def parse_pdf_bytes(file_bytes: bytes) -> str:
    """Core logic to parse PDF bytes, falling back to Gemini for OCR and embedded images."""
    native_text = ""

    # 1. Attempt Native Text Extraction
    try:
        pdf_reader = PdfReader(io.BytesIO(file_bytes))
        for page in pdf_reader.pages:
            native_text += page.extract_text() or ""
        native_text = " ".join(native_text.split())
    except Exception as e:
        app.logger.warning(f"pypdf native extraction failed: {e}")
        pass

    # 2. Hybrid Check and Fallback to Gemini
    if len(native_text) > NATIVE_TEXT_THRESHOLD:
        return native_text
    else:
        # Use the same image analysis prompt as it covers both OCR and visual description
        # We assume the PDF MIME type is handled by the model when passed as inlineData
        return analyze_image_bytes(file_bytes, "application/pdf")


def prettify_output(string: str) -> str:
    if not GEMINI_API_KEY:
        raise ValueError("Gemini API Key is not configured.")

    system_prompt = "You are an expert plain text to markdown converter. Convert and format the plain text as markdown for user convenience and readability. DO NOT CHANCE TEXT CONTENT and DO NOT MAKE COMMENTS, do your job and keep quiet."

    payload = {
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "contents": [
            {
                "parts": [
                    {"text": string},
                ]
            }
        ],
    }

    gemini_response = call_simple_gemini_api(payload)
    generated_text = (
        gemini_response.get("candidates", [{}])[0]
        .get("content", {})
        .get("parts", [{}])[0]
        .get("text", "")
    )

    if not generated_text:
        raise Exception("Gemini returned an empty transcription response.")

    return generated_text


# --- ADK Agent Logic ---


def ensure_session(app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID):
    """Create session if it doesn't exist, preventing termination issues."""
    session_payload = {"state": {}}
    resp = requests.post(
        f"{API_URL}/apps/{app_name}/users/{user_id}/sessions/{session_id}",
        json=session_payload,
    )
    if resp.status_code in (200, 201):
        app.logger.info("ADK Session ready.")
    elif resp.status_code == 409:
        app.logger.info("ADK Session already exists.")
    else:
        # If the session cannot be created or accessed, raise a critical error
        raise Exception(f"Failed to ensure ADK session: {resp.status_code} {resp.text}")


def callAgent(
    prompt: str, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
) -> Tuple[str, Optional[int]]:
    """
    Send prompt to ADK agent and return final string and HTTP status code.
    Allows for non-200 responses to be handled gracefully without crashing the pipeline.
    """
    try:
        ensure_session(app_name, user_id, session_id)
    except Exception as e:
        # Return a critical error if session setup fails (likely ADK server is down)
        return (
            f"AGENT CRITICAL ERROR: Could not establish session. ADK Server at {API_URL} may be offline. Detail: {e}",
            503,
        )

    payload = {
        # The ADK API requires the app_name (which is the root agent name)
        # to be repeated here in the body payload for consistency.
        "app_name": app_name,
        "user_id": user_id,
        "session_id": session_id,
        "new_message": {"role": "user", "parts": [{"text": prompt}]},
    }

    # Explicitly set content-type for robustness
    headers = {"Content-Type": "application/json"}

    try:
        # Add a timeout to prevent indefinite hanging
        response = requests.post(
            f"{API_URL}/run", json=payload, headers=headers, timeout=60
        )

        if response.status_code == 200:
            data = response.json()
            for event in reversed(data):
                content = event.get("content", {})
                parts = content.get("parts", [])
                for part in parts:
                    if "text" in part:
                        # Return the text and the successful status code
                        return part["text"].strip(), 200
            return "No text found in agent response.", 200
        else:
            # Return the error message and the failed status code
            return (
                f"Error {response.status_code}: {response.text}",
                response.status_code,
            )

    except requests.exceptions.ConnectionError:
        # Specific error if the ADK server is not reachable
        return (
            f"AGENT CRITICAL ERROR: Failed to connect to ADK Server at {API_URL}. Is the ADK server running?",
            503,
        )
    except requests.exceptions.Timeout:
        # Specific error if the request times out
        return (
            "AGENT CRITICAL ERROR: ADK Request timed out (over 60 seconds). Agent may be stuck.",
            504,
        )
    except Exception as e:
        # Catch any other unexpected request-related error
        return (
            f"AGENT CRITICAL ERROR: An unexpected error occurred during ADK request: {e}",
            500,
        )


def find_data_sufficiency(text):
    """Finds the data sufficiency statement."""
    mapping = {
        "SUFFICIENT DATA": "SUFFICIENT DATA",
        "INSUFFICIENT DATA": "INSUFFICIENT DATA",  # Added INSUFFICIENT DATA case
        "ACCEPT CASE": "ACCEPT CASE",
        "REJECT CASE": "REJECT CASE",
        "INCOMPLETE DATA": "INSUFFICIENT DATA",
    }

    # Updated pattern to capture all possible recommendation outcomes
    pattern = (
        r"(SUFFICIENT DATA|INSUFFICIENT DATA|ACCEPT CASE|REJECT CASE|INCOMPLETE DATA)"
    )
    match = re.search(pattern, text)
    if match:
        # Return the mapped value or the match itself if not in the map (safer)
        return mapping.get(match.group(1), match.group(1))
    return None


# --- Batch Processing and Pipeline Orchestration ---


def process_files_in_folder(folder_path: str) -> str:
    """Loads and parses all PDF, M4A, and image files in a folder."""
    combined_content = []

    if not os.path.isdir(folder_path):
        app.logger.error(f"Data folder not found at: {folder_path}. Cannot load files.")
        return "ERROR: Data folder not found."

    # Use glob to find all files in the directory
    file_paths = glob.glob(os.path.join(folder_path, "*"))

    if not file_paths:
        app.logger.warning("No files found in the data folder.")
        return "WARNING: No PDF or M4A files found in the folder."

    files_processed_count = 0

    for file_path in file_paths:
        file_name = os.path.basename(file_path)
        file_extension = file_name.lower().split(".")[-1]

        try:
            with open(file_path, "rb") as f:
                file_bytes = f.read()

            if file_extension == "pdf":
                print(f"-> Processing PDF file: {file_name}")
                content = parse_pdf_bytes(file_bytes)
                combined_content.append(
                    f"--- DOCUMENT ANALYSIS (PDF: {file_name}) ---\n{content}"
                )
                files_processed_count += 1

            elif file_extension == "m4a":
                print(f"-> Transcribing M4A file: {file_name}")
                content = transcribe_audio_bytes(file_bytes)
                combined_content.append(
                    f"--- TRANSCRIPT (M4A: {file_name}) ---\n{content}"
                )
                files_processed_count += 1

            elif file_extension in ["png", "jpg", "jpeg"]:
                mime_type = f"image/{file_extension}"
                print(f"-> Analyzing Image file: {file_name}")
                content = analyze_image_bytes(file_bytes, mime_type)
                combined_content.append(
                    f"--- IMAGE ANALYSIS ({file_name}) ---\n{content}"
                )
                files_processed_count += 1

            else:
                print(f"-> Skipping unsupported file type: {file_name}")

        except Exception as e:
            app.logger.error(f"Failed to process file {file_name}: {e}")
            combined_content.append(f"--- ERROR PROCESSING {file_name} --- Error: {e}")

    if files_processed_count == 0:
        return "WARNING: No supported files (PDF, M4A, PNG, JPG) were processed."

    return "\n\n".join(combined_content)


def run_claim_pipeline() -> List[Dict[str, str]]:
    """
    Executes the multi-step claims processing pipeline.
    """
    global pipeline_result_store
    pipeline_result_store = []

    # 1. Load and process all client data from the local folder
    app.logger.info("--- STEP 0: Data Ingestion and Pre-processing ---")
    initial_data = process_files_in_folder(DATA_FOLDER)

    if "ERROR:" in initial_data or "WARNING:" in initial_data:
        pipeline_result_store.append(
            {"step": "0. Ingestion", "status": "ERROR", "result": initial_data}
        )
        return pipeline_result_store

    # 2. STEP 1: Initial Case Acceptance/Rejection
    app.logger.info(
        "--- STEP 1: Initial Case Acceptance/Rejection (evidence_sorter_initial) ---"
    )

    # The prompt must tell the coordinator which sub-agent to use
    step1_prompt = (
        f"Case Data for Initial Review:\n\n{initial_data}\n\nAction: Sort_Initial"
    )

    step1_result, status = callAgent(
        step1_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {"step": "1. Initial Review", "status": "ADK ERROR", "result": step1_result}
        )
        return pipeline_result_store

    # Check the result of the initial sort for case status
    recommendation = find_data_sufficiency(step1_result)

    if recommendation in ["REJECT CASE", "INSUFFICIENT DATA"]:
        status_label = (
            "REJECTED" if recommendation == "REJECT CASE" else "INSUFFICIENT DATA"
        )
        final_output = delimit_output_string(step1_result)
        pipeline_result_store.append(
            {
                "step": "1. Initial Review",
                "status": status_label,
                "result": final_output,
            }
        )
        app.logger.info(f"Pipeline stopped: {status_label}")
        return pipeline_result_store

    final_output = delimit_output_string(step1_result)
    pipeline_result_store.append(
        {
            "step": "1. Initial Review",
            "status": "ACCEPTED/SUFFICIENT",
            "result": final_output,
        }
    )

    # The pipeline continues if accepted and sufficient data is present
    previous_step_summary = final_output

    # 3. STEP 2: Detailed Evidence Sorting - Phase 1 (Witness/Interviews)
    app.logger.info(
        "--- STEP 2: Detailed Evidence Sorting - Phase 1 (evidence_sorter_1) ---"
    )

    # Pass the initial data along with the output from the previous step
    step2_input = f"Initial Summary:\n{previous_step_summary}\n\nNew/Combined Data:\n{initial_data}"
    step2_prompt = f"{step2_input}\n\nAction: Wraggler1"

    step2_result, status = callAgent(
        step2_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "2. Evidence Sort 1",
                "status": "ADK ERROR",
                "result": step2_result,
            }
        )
        return pipeline_result_store

    final_output = delimit_output_string(step2_result)
    pipeline_result_store.append(
        {"step": "2. Evidence Sort 1", "status": "COMPLETE", "result": final_output}
    )
    previous_step_summary = final_output

    # 4. STEP 3: Detailed Evidence Sorting - Phase 2 (Medical/Legal Verification)
    app.logger.info(
        "--- STEP 3: Detailed Evidence Sorting - Phase 2 (evidence_sorter_2) ---"
    )

    step3_input = f"Previous Sort 1 Result:\n{previous_step_summary}\n\nCombined Raw Data:\n{initial_data}"
    step3_prompt = f"{step3_input}\n\nAction: Wraggler2"

    step3_result, status = callAgent(
        step3_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "3. Evidence Sort 2",
                "status": "ADK ERROR",
                "result": step3_result,
            }
        )
        return pipeline_result_store

    final_output = delimit_output_string(step3_result)
    pipeline_result_store.append(
        {"step": "3. Evidence Sort 2", "status": "COMPLETE", "result": final_output}
    )
    previous_step_summary = final_output

    # 5. STEP 4: Final Evidence Synthesis
    app.logger.info("--- STEP 4: Final Evidence Synthesis (evidence_sorter_3) ---")

    step4_input = f"Results from Sort 2 Verification:\n{previous_step_summary}\n\nOriginal Raw Data:\n{initial_data}"
    step4_prompt = f"{step4_input}\n\nAction: Wraggler3"

    step4_result, status = callAgent(
        step4_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "4. Final Synthesis",
                "status": "ADK ERROR",
                "result": step4_result,
            }
        )
        return pipeline_result_store

    final_output = delimit_output_string(step4_result)
    pipeline_result_store.append(
        {"step": "4. Final Synthesis", "status": "COMPLETE", "result": final_output}
    )

    app.logger.info("--- Pipeline Completed Successfully ---")
    return pipeline_result_store


# --- Flask Routes ---


@app.route("/run_batch_pipeline", methods=["POST"])
def run_pipeline_endpoint():
    """Endpoint to trigger the full claims pipeline."""
    try:
        results = run_claim_pipeline()
        return jsonify(results), 200
    except Exception as e:
        app.logger.error(
            f"Critical error during pipeline execution: {e}", exc_info=True
        )
        return (
            jsonify({"error": f"Internal Server Error during pipeline run: {e}"}),
            500,
        )


@app.route("/pipeline_results", methods=["GET"])
def get_pipeline_results():
    """Endpoint to retrieve the last pipeline run's results."""
    # This route is intended for a frontend to poll or fetch the final state.
    if not pipeline_result_store:
        return jsonify({"message": "Pipeline has not been run yet."}), 200
    return jsonify(pipeline_result_store), 200


@app.route("/health", methods=["GET"])
def health_check():
    """Basic health check to confirm Flask is running."""
    return jsonify({"status": "ok", "app": APP_NAME}), 200


@app.post("/sanity")
def sanity() -> str:
    print(request.files.getlist("files[]"))
    return "sus"


@app.post("/1")
def run_1() -> List[Dict[str, str]]:
    """
    Executes the multi-step claims processing pipeline.
    """
    global pipeline_result_store
    global file_context
    file_context = 0
    nuke_files()
    pipeline_result_store = []

    # 1. Load and process all client data from the local folder
    app.logger.info("--- STEP 0: Data Ingestion and Pre-processing ---")
    uploaded_files = request.files.getlist("files[]")
    save_files(uploaded_files)

    initial_data = process_files_in_folder(DATA_FOLDER)
    file_context = initial_data

    if "ERROR:" in initial_data or "WARNING:" in initial_data:
        pipeline_result_store.append(
            {
                "step": "0. Ingestion",
                "status": "ERROR",
                "result": initial_data,
                "good": False,
            }
        )
        return pipeline_result_store[-1]

    # 2. STEP 1: Initial Case Acceptance/Rejection
    app.logger.info(
        "--- STEP 1: Initial Case Acceptance/Rejection (evidence_sorter_initial) ---"
    )

    # The prompt must tell the coordinator which sub-agent to use
    step1_prompt = (
        f"Case Data for Initial Review:\n\n{initial_data}\n\nAction: Sort_Initial"
    )

    step1_result, status = callAgent(
        step1_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    step1_result = prettify_output(step1_result)

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "1. Initial Review",
                "status": "ADK ERROR",
                "result": step1_result,
                "good": False,
            }
        )
        return pipeline_result_store

    # Check the result of the initial sort for case status
    recommendation = find_data_sufficiency(step1_result)

    if recommendation in ["REJECT CASE", "INSUFFICIENT DATA"]:
        status_label = (
            "REJECTED" if recommendation == "REJECT CASE" else "INSUFFICIENT DATA"
        )
        final_output = step1_result
        pipeline_result_store.append(
            {
                "step": "1. Initial Review",
                "status": status_label,
                "result": final_output,
                "good": False,
            }
        )
        app.logger.info(f"Pipeline stopped: {status_label}")
        return pipeline_result_store[-1]

    final_output = step1_result
    pipeline_result_store.append(
        {
            "step": "1. Initial Review",
            "status": "ACCEPTED/SUFFICIENT",
            "result": final_output,
            "good": True,
        }
    )

    return pipeline_result_store[-1]


@app.post("/2")
def run_2() -> List[Dict[str, str]]:
    global pipeline_result_store
    global file_context

    uploaded_files = request.files.getlist("files[]")
    nuke_files()
    save_files(uploaded_files)

    file_context += process_files_in_folder(DATA_FOLDER)
    initial_data = file_context

    final_output = pipeline_result_store[-1]["result"]

    # The pipeline continues if accepted and sufficient data is present
    previous_step_summary = final_output

    step2_input = f"Initial Summary:\n{previous_step_summary}\n\nNew/Combined Data:\n{initial_data}"

    # 3. STEP 2: Detailed Evidence Sorting - Phase 1 (Witness/Interviews)
    app.logger.info(
        "--- STEP 2: Detailed Evidence Sorting - Phase 1 (evidence_sorter_1) ---"
    )

    # Pass the initial data along with the output from the previous step
    step2_input = f"Initial Summary:\n{previous_step_summary}\n\nNew/Combined Data:\n{initial_data}"
    step2_prompt = f"{step2_input}\n\nAction: Wraggler1"

    step2_result, status = callAgent(
        step2_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "2. Evidence Sort 1",
                "status": "ADK ERROR",
                "result": step2_result,
                "good": False,
            }
        )
        return pipeline_result_store[-1]

    recommendation = find_data_sufficiency(step2_result)

    if recommendation in ["REJECT CASE", "INSUFFICIENT DATA"]:
        status_label = (
            "REJECTED" if recommendation == "REJECT CASE" else "INSUFFICIENT DATA"
        )
        final_output = step2_result
        pipeline_result_store.append(
            {
                "step": "2. Evidence Sort 1",
                "status": status_label,
                "result": prettify_output(step2_result),
                "good": False,
            }
        )
        app.logger.info(f"Pipeline stopped: {status_label}")
        return pipeline_result_store[-1]

    final_output = delimit_output_string(step2_result)
    pipeline_result_store.append(
        {
            "step": "2. Evidence Sort 1",
            "status": "COMPLETE",
            "result": prettify_output(final_output),
            "good": True,
        }
    )
    previous_step_summary = final_output

    return pipeline_result_store[-1]


@app.post("/3")
def run_3() -> List[Dict[str, str]]:
    global pipeline_result_store
    global file_context

    uploaded_files = request.files.getlist("files[]")
    nuke_files()
    save_files(uploaded_files)

    file_context += process_files_in_folder(DATA_FOLDER)

    initial_data = file_context

    # 4. STEP 3: Detailed Evidence Sorting - Phase 2 (Medical/Legal Verification)
    app.logger.info(
        "--- STEP 3: Detailed Evidence Sorting - Phase 2 (evidence_sorter_2) ---"
    )

    previous_step_summary = pipeline_result_store[-1]["result"]

    step3_input = f"Previous Sort 1 Result:\n{previous_step_summary}\n\nCombined Raw Data:\n{initial_data}"
    step3_prompt = f"{step3_input}\n\nAction: Wraggler2"

    step3_result, status = callAgent(
        step3_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "3. Evidence Sort 2",
                "status": "ADK ERROR",
                "result": prettify_output(step3_result),
                "good": False,
            }
        )
        return pipeline_result_store[-1]

    recommendation = find_data_sufficiency(step3_result)

    if recommendation in ["REJECT CASE", "INSUFFICIENT DATA"]:
        status_label = (
            "REJECTED" if recommendation == "REJECT CASE" else "INSUFFICIENT DATA"
        )
        final_output = step3_result
        pipeline_result_store.append(
            {
                "step": "3. Evidence Sort 2",
                "status": status_label,
                "result": prettify_output(final_output),
                "good": False,
            }
        )
        app.logger.info(f"Pipeline stopped: {status_label}")
        return pipeline_result_store[-1]

    final_output = delimit_output_string(step3_result)
    pipeline_result_store.append(
        {
            "step": "3. Evidence Sort 2",
            "status": "COMPLETE",
            "result": prettify_output(final_output),
            "good": True,
        }
    )
    previous_step_summary = final_output

    return pipeline_result_store[-1]


@app.post("/4")
def run_4() -> List[Dict[str, str]]:
    global pipeline_result_store
    global file_context

    uploaded_files = request.files.getlist("files[]")
    nuke_files()
    save_files(uploaded_files)

    file_context += process_files_in_folder(DATA_FOLDER)

    initial_data = file_context

    # 5. STEP 4: Final Evidence Synthesis
    app.logger.info("--- STEP 4: Final Evidence Synthesis (evidence_sorter_3) ---")

    previous_step_summary = ""
    for step in pipeline_result_store:
        previous_step_summary += step["step"] + " -> " + step["result"] + "\n\n"

    step4_input = f"Results from Sort 3 Verification:\n{previous_step_summary}\n\nOriginal Raw Data:\n{initial_data}"
    step4_prompt = f"{step4_input}\n\nAction: Wraggler3"

    step4_result, status = callAgent(
        step4_prompt, app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )

    if status != 200:
        pipeline_result_store.append(
            {
                "step": "4. Final Synthesis",
                "status": "ADK ERROR",
                "result": prettify_output(step4_result),
                "good": False,
            }
        )
        return pipeline_result_store[-1]

    final_output = delimit_output_string(step4_result)

    pros = (
        call_gemini(
            {
                "systemInstruction": {
                    "parts": [
                        {
                            "text": "You will be given information on a plaintiff law case. You will be given  an summary of the case with a recommended action. Upon reading the information decide and explain your reasoning on why the case SHOULD be taken on"
                        }
                    ]
                },
                "contents": [
                    {
                        "parts": [
                            {"text": final_output},
                        ]
                    }
                ],
            }
        ),
    )

    cons = (
        call_gemini(
            {
                "systemInstruction": {
                    "parts": [
                        {
                            "text": "You will be given information on a plaintiff law case. You will be given  an summary of the case with a recommended action. Upon reading the information decide and explain your reasoning on why the case should NOT be taken on"
                        }
                    ]
                },
                "contents": [
                    {
                        "parts": [
                            {"text": final_output},
                        ]
                    }
                ],
            },
        ),
    )

    percent = (
        call_gemini(
            {
                "systemInstruction": {
                    "parts": [
                        {
                            "text": "You will be given information on a plaintiff law case. You will be given  an summary of the case with a recommended action. Upon reading the information decide on a percentage value from 0-100% to determine the value of the case from a law firm perspective. On the line immediately following write an explanation as to why you decided to rate the case that percentage value"
                        }
                    ]
                },
                "contents": [
                    {
                        "parts": [
                            {"text": final_output},
                        ]
                    }
                ],
            }
        ),
    )

    pipeline_result_store.append(
        {
            "step": "4. Final Synthesis",
            "status": "COMPLETE",
            "result": final_output,
            "good": True,
            "pros": pros,
            "cons": cons,
            "percent": percent,
        }
    )

    app.logger.info("--- Pipeline Completed Successfully ---")
    return pipeline_result_store[-1]


if __name__ == "__main__":
    # Create the data folder if it doesn't exist to prevent file I/O errors
    if not os.path.exists(DATA_FOLDER):
        os.makedirs(DATA_FOLDER)
        print(f"Created data folder: {DATA_FOLDER}")

    print(f"\n--- Starting Progressive Claims ADK Runner ---\n")
    print(f"ADK Agent: {APP_NAME}")
    print(f"ADK Server URL: {API_URL}")
    print(f"Flask Runner URL: http://127.0.0.1:5000/run_batch_pipeline")
    print(f"Waiting for ADK Server to start on {API_URL}...")

    # Set up basic logging
    import logging

    app.logger.setLevel(logging.INFO)

    # Run Flask application
    app.run(debug=True, port=5000, use_reloader=False)
