import requests

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


#======================
# AGENT PIPELINE
#======================
parsedText = """
Uh, yeah, this was on I-95 near the exit to Coconut Creek. The other driver hit my side door and then took off. My shoulder slammed into the window, and it’s been sore ever since. The car had to be towed — we’ve got photos of that.

A state trooper came later and took some info; he gave me a small slip with a number, but I haven’t received any full report yet.

I went to Broward UrgentCare the next day because it hurt to move my arm. The doctor said it’s probably just inflammation, prescribed ibuprofen, and said to rest it for a week. Didn’t do any scans since it didn’t look like a break.

Files uploaded: “TowSlip.jpg”, “CarPhotos.zip”, “UrgentCare_Broward.pdf”.
"""

parsedText += "\n\nAction: Sort"

#======================
# RUN AGENT
#======================
if __name__ == "__main__":
    result = callAgent(parsedText)
    print("Agent Output:\n")
    print(result)
