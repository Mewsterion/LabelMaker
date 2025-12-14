import os
import base64
import requests
from flask import Flask, request, jsonify, send_from_directory
from dotenv import load_dotenv
from flask_cors import CORS

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for local development

API_KEY = os.getenv("EASYPOST_API_KEY")
CARRIER_ACCOUNT_ID = os.getenv("EASYPOST_CARRIER_ACCOUNT_ID")

if not API_KEY or not CARRIER_ACCOUNT_ID:
    print("❌ Error: API keys not found in .env file.")
    print("Please ensure .env exists with EASYPOST_API_KEY and EASYPOST_CARRIER_ACCOUNT_ID")

@app.route('/')
def index():
    return send_from_directory('.', 'LabelMaker.html')

@app.route('/create_label', methods=['POST'])
def create_label():
    try:
        data = request.json
        
        # Inject the carrier account ID from env if not present (or just override it)
        # The frontend sends the whole shipment object, we need to ensure carrier_accounts is set correctly
        if 'shipment' in data:
            data['shipment']['carrier_accounts'] = [CARRIER_ACCOUNT_ID]
            
            # Inject from_address from environment variables
            data['shipment']['from_address'] = {
                "name": os.getenv("RETURN_ADDRESS_NAME"),
                "street1": os.getenv("RETURN_ADDRESS_STREET1"),
                "city": os.getenv("RETURN_ADDRESS_CITY"),
                "state": os.getenv("RETURN_ADDRESS_STATE"),
                "zip": os.getenv("RETURN_ADDRESS_ZIP"),
                "country": os.getenv("RETURN_ADDRESS_COUNTRY", "US"),
                "phone": os.getenv("RETURN_ADDRESS_PHONE")
            }
        
        # Prepare the request to EasyPost
        url = 'https://api.easypost.com/v2/shipments'
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Basic ' + base64.b64encode(f"{API_KEY}:".encode()).decode()
        }
        
        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code != 200 and response.status_code != 201:
            return jsonify(response.json()), response.status_code
            
        return jsonify(response.json())

    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

# --- Local Label Generation (ReportLab) ---
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
import uuid

def generate_local_pdf(destination_address, output_filename):
    """Generates a 6x4 inch horizontal shipping label as a PDF."""
    label_width = 6 * inch
    label_height = 4 * inch
    c = canvas.Canvas(output_filename, pagesize=(label_width, label_height))

    # Return Address
    return_address = [
        os.getenv("RETURN_ADDRESS_NAME", "Sender Name"),
        os.getenv("RETURN_ADDRESS_STREET1", "Sender Street"),
        os.getenv("RETURN_ADDRESS_CITY_STATE_ZIP", "Sender City, State Zip")
    ]
    c.setFont("Helvetica", 10)
    return_text = c.beginText()
    return_text.setTextOrigin(0.25 * inch, 3.5 * inch)
    for line in return_address:
        return_text.textLine(line)
    c.drawText(return_text)

    # Destination Address
    font_size = 14
    line_spacing = 1.2
    line_height = font_size * line_spacing
    c.setFont("Helvetica-Bold", font_size)
    
    dest_lines = destination_address.strip().split('\n')
    total_text_height = len(dest_lines) * line_height
    start_y = (label_height / 2) + (total_text_height / 2) - line_height
    
    longest_line = max(dest_lines, key=len) if dest_lines else ""
    text_width = c.stringWidth(longest_line, "Helvetica-Bold", font_size)
    start_x = (label_width - text_width) / 2
    
    dest_text = c.beginText()
    dest_text.setTextOrigin(start_x, start_y)
    dest_text.setLeading(line_height)
    for line in dest_lines:
        dest_text.textLine(line.strip())
    c.drawText(dest_text)
    c.save()

@app.route('/create_local_label', methods=['POST'])
def create_local_label():
    try:
        data = request.json
        # Extract address from the shipment object structure we use in frontend
        # data['shipment']['to_address'] contains the parts.
        # We need to reconstruct the string for the PDF generator or just use the raw text if sent.
        # Let's assume the frontend sends the formatted address string or we build it.
        
        # Option A: Reconstruct from components
        to_addr = data.get('shipment', {}).get('to_address', {})
        name = to_addr.get('name', '')
        street1 = to_addr.get('street1', '')
        street2 = to_addr.get('street2', '')
        city = to_addr.get('city', '')
        state = to_addr.get('state', '')
        zip_code = to_addr.get('zip', '')
        
        address_lines = [name, street1]
        if street2:
            address_lines.append(street2)
        address_lines.append(f"{city}, {state} {zip_code}")
        
        full_address = "\n".join(address_lines)
        
        # Generate filename
        filename = f"label_{uuid.uuid4().hex}.pdf"
        filepath = os.path.join('.', filename)
        
        generate_local_pdf(full_address, filepath)
        
        # Return URL to download
        return jsonify({
            "postage_label": {
                "label_url": f"/download/{filename}"
            },
            "tracker": {
                "public_url": "N/A (Local Label)"
            }
        })

    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

@app.route('/download/<filename>')
def download_file(filename):
    return send_from_directory('.', filename)


if __name__ == '__main__':
    print("🚀 LabelMaker Server running at http://localhost:5000")
    app.run(debug=True, port=5000)
