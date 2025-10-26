import requests
import json
import logging
import sys
from flask import Flask, jsonify, request

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# --- Configuration ---
# The URL for the ADK Web Server (where 'adk web agents' is running)
ADK_SERVER_URL = "http://127.0.0.1:8000"

# The name of the root agent (or the folder name the ADK loaded from)
AGENT_APP_NAME = "agents"

# User and session IDs for the pipeline run (These will remain constant for a given claim)
USER_ID = "progressive_user_1"
SESSION_ID = "s_progressive_claim_1"
# ---------------------

# GLOBAL STATE STORE: Stores the cumulative summary after each stage.
# In a production environment, this would use a proper database (like Firestore or Redis).
# Key: SESSION_ID, Value: cumulative summary string
case_state = {}


def run_agent_step(
    step_name: str, input_data: str, is_final_synthesis: bool = False
) -> dict:
    """
    Sends a request to the ADK server to run a specific agent step.
    The input_data is the cumulative text from all previous stages (managed by Flask).
    """

    # Construct the full endpoint URL for the agent's run method
    run_url = f"{ADK_SERVER_URL}/run"

    # The agent input is wrapped in a dictionary expected by the ADK agent
    agent_input = {"document_text": input_data}

    # --- Special Formatting for Final Synthesis (Stage 4) ---
    if is_final_synthesis:
        # Instruct the agent to use specific delimiters for easy front-end parsing.
        delimiter_instruction = (
            "Based on the combined case information, perform a final synthesis. "
            "Your output MUST be structured using the following specific delimiters: "
            "1. Case status (ACCEPTED or REJECTED) inside <STATUS>...</STATUS> tags. "
            "2. Success percentage (e.g., 75%) inside <PERCENTAGE>...</PERCENTAGE> tags. "
            "3. A list of key PROS for the case inside <PROS>...</PROS> tags. "
            "4. A list of key CONS for the case inside <CONS>...</CONS> tags. "
            "The document text is provided below:\n\n"
        )
        # Prepend the instruction to the document text
        agent_input["document_text"] = delimiter_instruction + input_data
    # -----------------------------------------------

    payload = {
        "app_name": AGENT_APP_NAME,
        "step_name": step_name,
        "user_id": USER_ID,
        "session_id": SESSION_ID,
        "input_data": agent_input,
    }

    logger.info(f"Running step '{step_name}' with app name '{AGENT_APP_NAME}'...")

    try:
        # Make the POST request to the ADK server
        response = requests.post(
            run_url, json=payload, headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        # The ADK response contains 'text' and 'status'
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error running step '{step_name}': {e}")
        logger.error(f"Request Payload: {json.dumps(payload, indent=2)}")
        if "response" in locals() and response.text:
            logger.error(f"ADK Server Response Content: {response.text}")
        raise e


# --- Helper function to get the current cumulative case summary ---
def get_cumulative_input(new_document_text: str) -> str:
    """Combines the previous summary with the new document text."""
    previous_summary = case_state.get(SESSION_ID, "")

    if not previous_summary:
        # If no summary exists, this is the first stage.
        logger.info("Starting new case state.")
        return new_document_text
    else:
        # For subsequent stages, append the new data to the previous summary.
        logger.info("Combining previous state with new evidence.")
        return (
            f"--- CUMULATIVE CASE SUMMARY FROM PREVIOUS STAGE ---\n"
            f"{previous_summary}\n"
            f"--- NEW EVIDENCE UPLOADED ---\n"
            f"{new_document_text}"
        )


# --- API Endpoints for UI Stages (Managing state after each successful agent run) ---


@app.route("/stage1_initial_review", methods=["POST"])
def stage1_initial_review():
    """
    Stage 1: Initial review. Expects ONLY the new file text.
    """
    try:
        # Extract the content of the new files uploaded for this stage
        new_document_text = request.json.get("document_text")
        if not new_document_text:
            return jsonify(
                {"error": "Missing 'document_text' (new file content) in request body."}
            ), 400

        # Combine the new text with the (empty) previous state
        input_for_agent = get_cumulative_input(new_document_text)

        # Run Agent step 1
        result = run_agent_step("initial_review", input_for_agent)

        output_text = result.get("text", "")

        # UPDATE STATE: Store the new summary for the next stage
        case_state[SESSION_ID] = output_text

        return jsonify(
            {
                "stage": 1,
                "status": result.get("status", "ERROR"),
                "output_text": output_text,
            }
        )
    except Exception as e:
        logger.error(f"Stage 1 failed: {e}", exc_info=True)
        return jsonify({"error": f"Stage 1 failed: {e}"}), 500


@app.route("/stage2_evidence_sort_1", methods=["POST"])
def stage2_evidence_sort_1():
    """
    Stage 2: First evidence sort. Expects ONLY the new file text.
    """
    try:
        new_document_text = request.json.get("document_text")
        if not new_document_text:
            return jsonify(
                {"error": "Missing 'document_text' (new file content) in request body."}
            ), 400

        # Flask combines the previous summary (Stage 1 output) with the new text
        input_for_agent = get_cumulative_input(new_document_text)

        # Run Agent step 2
        result = run_agent_step("evidence_sort_1", input_for_agent)

        output_text = result.get("text", "")

        # UPDATE STATE: Store the new summary for the next stage
        case_state[SESSION_ID] = output_text

        return jsonify(
            {
                "stage": 2,
                "status": result.get("status", "ERROR"),
                "output_text": output_text,
            }
        )
    except Exception as e:
        logger.error(f"Stage 2 failed: {e}", exc_info=True)
        return jsonify({"error": f"Stage 2 failed: {e}"}), 500


@app.route("/stage3_evidence_sort_2", methods=["POST"])
def stage3_evidence_sort_2():
    """
    Stage 3: Second evidence sort. Expects ONLY the new file text.
    """
    try:
        new_document_text = request.json.get("document_text")
        if not new_document_text:
            return jsonify(
                {"error": "Missing 'document_text' (new file content) in request body."}
            ), 400

        # Flask combines the previous summary (Stage 2 output) with the new text
        input_for_agent = get_cumulative_input(new_document_text)

        # Run Agent step 3
        result = run_agent_step("evidence_sort_2", input_for_agent)

        output_text = result.get("text", "")

        # UPDATE STATE: Store the new summary for the next stage
        case_state[SESSION_ID] = output_text

        return jsonify(
            {
                "stage": 3,
                "status": result.get("status", "ERROR"),
                "output_text": output_text,
            }
        )
    except Exception as e:
        logger.error(f"Stage 3 failed: {e}", exc_info=True)
        return jsonify({"error": f"Stage 3 failed: {e}"}), 500


@app.route("/stage4_final_synthesis", methods=["POST"])
def stage4_final_synthesis():
    """
    Stage 4: Final Synthesis. Expects ONLY the final file text (if any) or an empty body.
    Runs on the full accumulated context from all previous stages.
    """
    try:
        # Extract final input. We use a default empty string if no content is provided.
        new_document_text = request.json.get("document_text", "")

        # Flask combines the previous summary (Stage 3 output) with any final new text
        input_for_agent = get_cumulative_input(new_document_text)

        # Check if there is any data to run the final synthesis on
        if not input_for_agent:
            return jsonify(
                {"error": "No accumulated case data to run final synthesis."}
            ), 400

        # Run Agent step 4 - Set is_final_synthesis=True to inject the delimiter instruction
        result = run_agent_step(
            "final_synthesis", input_for_agent, is_final_synthesis=True
        )

        output_text = result.get("text", "")

        # Cleanup state: Remove the session's state data after the final stage is complete
        if SESSION_ID in case_state:
            del case_state[SESSION_ID]
            logger.info(f"Local Flask case state for session '{SESSION_ID}' cleared.")

        return jsonify(
            {
                "stage": 4,
                "status": result.get("status", "ERROR"),
                # This output will contain the <STATUS>, <PERCENTAGE>, <PROS>, <CONS> tags.
                "output_text": output_text,
            }
        )
    except Exception as e:
        logger.error(f"Stage 4 failed: {e}", exc_info=True)
        return jsonify({"error": f"Stage 4 failed: {e}"}), 500


# --- Deprecated Batch Pipeline ---
@app.route("/run_batch_pipeline", methods=["POST"])
def run_batch_pipeline_deprecated():
    """
    Deprecated: This was the original batch pipeline.
    """
    return jsonify(
        {
            "message": "Use /stage1_initial_review, /stage2_evidence_sort_1, etc., for sequential claim processing."
        }
    ), 400


# --- Session Management (Retained) ---

if __name__ == "__main__":
    # Initialize session state before starting the application

    # Attempt to delete the session first to ensure a clean run
    try:
        delete_url = f"{ADK_SERVER_URL}/apps/{AGENT_APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
        response = requests.delete(delete_url)
        if response.status_code == 200:
            logger.info(f"Existing ADK session '{SESSION_ID}' deleted successfully.")
        else:
            logger.warning(
                f"Failed to delete existing ADK session or session did not exist. Status: {response.status_code}"
            )

        # Create a new session
        create_url = f"{ADK_SERVER_URL}/apps/{AGENT_APP_NAME}/users/{USER_ID}/sessions/{SESSION_ID}"
        response = requests.post(create_url)
        response.raise_for_status()
        logger.info(f"New ADK session '{SESSION_ID}' created successfully.")

        # Also clear the local Flask state for a clean start
        case_state[SESSION_ID] = ""
        logger.info("Local Flask case state initialized.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Critical error during session initialization/cleanup: {e}")
        sys.exit(1)

    # Note: Flask's built-in run method is typically used in development.
    # We set use_reloader=False to prevent the app from initializing the ADK session twice.
    app.run(debug=True, use_reloader=False)
