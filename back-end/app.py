from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
import io

app = Flask(__name__)

@app.route('/upload', methods=['POST'])
def upload_pdf():
    # Ensure a file was sent
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']

    # Ensure it's a PDF
    if not file.filename.lower().endswith('.pdf'):
        return jsonify({"error": "File must be a PDF"}), 400

    # Read PDF content from memory
    pdf_bytes = file.read()
    reader = PdfReader(io.BytesIO(pdf_bytes))

    # Extract text from all pages
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""

    return jsonify({"text": text})
    

if __name__ == '__main__':
    app.run(debug=True)
