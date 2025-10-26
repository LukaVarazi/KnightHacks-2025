import re

def delimit_output_string(output_text: str) -> str:
    """
    Separates values in an assorted output text blob by placing a
    'thinking face' emoji (🤔) next to a simplified set of keywords and patterns.

    Args:
        output_text: The assorted string blob from the backend.

    Returns:
        The modified string with emojis acting as delimiters.
    """
    # Define the 'thinking face' emoji
    DELIMITER_EMOJI = " 🤔" # Note the leading space for clean separation

    # --- Handle fixed keywords (Case-insensitive for approved/denied) ---

    # 1. 'approved'
    output_text = re.sub(r'(approved)', r'\1' + DELIMITER_EMOJI, output_text, flags=re.IGNORECASE)

    # 2. 'denied'
    output_text = re.sub(r'(denied)', r'\1' + DELIMITER_EMOJI, output_text, flags=re.IGNORECASE)

    # 3. 'Pros' (using word boundary \b to ensure it matches the whole word)
    output_text = re.sub(r'\b(Pros)\b', r'\1' + DELIMITER_EMOJI, output_text)

    # 4. 'Cons' (using word boundary \b)
    output_text = re.sub(r'\b(Cons)\b', r'\1' + DELIMITER_EMOJI, output_text)

    # --- Handle a single percentage value ---

    # 5. The 2-digit number followed by a '%' sign (e.g., "85%").
    # All previous logic for P.B.S. has been removed.
    output_text = re.sub(r'(\d{2}%)', r'\1' + DELIMITER_EMOJI, output_text)

    return output_text

# --- Quick Test Block ---

if __name__ == "__main__":
    # Sample input string using only the requested set of values
    sample_input = (
        "The decision was Approved. The score is 92%. "
        "Here are the points: Pros. The application had no major Cons. "
        "A small note mentions a potential Denied status for future similar cases."
    )

    modified_output = delimit_output_string(sample_input)

    print("\n" + "="*60)
    print("REVISED DELIMITER CONSOLE TEST OUTPUT")
    print("="*60)
    print("Original:\n", sample_input)
    print("\nModified (Delimited):\n", modified_output)
    print("="*60 + "\n")