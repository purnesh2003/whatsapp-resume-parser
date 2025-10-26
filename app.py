# =========================================================================
# WA RESUME PARSER - FLASK WEBHOOK (FINAL CLEAN VERSION)
# =========================================================================
import os
import json
import gspread 
import requests
import mimetypes
from datetime import datetime
from dotenv import load_dotenv

from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from pydantic import BaseModel, Field
from openai import OpenAI
from openai import APIError # Import specific exception class

# Load environment variables from .env file
load_dotenv()

# --- 1. DATA MODEL (Pydantic for Structured AI Output) ---
class ResumeData(BaseModel):
    """Defines the structured schema for data extracted by the LLM."""
    name: str = Field(description="The full name of the candidate.")
    email: str = Field(description="The primary email address.")
    phone: str = Field(description="The primary contact phone number, including country code.")
    key_skills: list[str] = Field(description="A list of 3-5 most relevant technical or professional skills.")
    education: str = Field(description="Highest level of education (degree and institution).")

# --- 2. LLM PARSING FUNCTION (CORRECTED JSON MODE) ---
def parse_with_openai(text_content):
    """Uses OpenAI's GPT-3.5-turbo to extract structured data from resume text using native JSON mode."""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except Exception:
        print("Error: OPENAI_API_KEY not found or invalid.")
        return None
    
    # Generate the schema description string to include in the prompt
    schema_desc = json.dumps(ResumeData.model_json_schema(), indent=2)
    
    system_prompt = (
        "You are an expert resume parser. Your response MUST be a JSON object "
        "that strictly adheres to the following JSON schema. Do not include any text outside the JSON block.\n\n"
        f"JSON SCHEMA:\n{schema_desc}"
    )
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo", # Universally accessible model
            response_format={"type": "json_object"}, # NATIVE JSON mode
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Resume Text:\n\n{text_content}"}
            ]
        )
        
        # The response content is a raw JSON string, so we parse it
        json_data = json.loads(response.choices[0].message.content)
        
        # Validate and return the data using Pydantic
        return ResumeData(**json_data).model_dump()

    except APIError as e:
        # --- NEW CODE: Catch the specific Quota Error (429) ---
        if e.code == 'insufficient_quota':
            print(f"OpenAI Quota Error: {e.message}")
            return {'error': 'quota_exceeded'} # Return a specific error flag
        
        print(f"OpenAI API Error: {e}")
        return None

    except Exception as e:
        print(f"OpenAI Parsing Error (General): {e}")
        return None


# --- 3. CORE APPLICATION SETUP ---
app = Flask(__name__)

# Twilio Client Initialization
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_CLIENT = Client(TWILIO_SID, TWILIO_AUTH)

# Path Setup for client_secret.json 
BASE_DIR = os.path.dirname(os.path.abspath(__file__)) 
CLIENT_SECRET_PATH = os.path.join(BASE_DIR, 'client_secret.json')

# Gspread Initialization
SHEET = None
try:
    GC = gspread.service_account(filename=CLIENT_SECRET_PATH)
    sheet_id = os.getenv("GOOGLE_SHEET_NAME").strip('"') 
    
    # Use open_by_key() with the ID
    SPREADSHEET = GC.open_by_key(sheet_id)
    
    # IMPORTANT: Access the first worksheet. Change "sheet1" if you renamed the tab.
    SHEET = SPREADSHEET.sheet1 
    
    print("✅ Google Sheets connection successful.")
    
except Exception as e:
    print(f"❌ Google Sheets Setup Failed: {e}")
    SHEET = None


# --- 4. UTILITY FUNCTIONS ---

def download_media(media_url, content_type):
    """Downloads media from Twilio's URL using basic authentication."""
    auth_header = (TWILIO_SID, TWILIO_AUTH)
    
    response = requests.get(media_url, auth=auth_header)
    
    if response.status_code == 200:
        file_extension = mimetypes.guess_extension(content_type) or '.dat'
        return response.content, file_extension
    return None, None

def convert_to_text(file_content, file_ext):
    """
    Placeholder for file-to-text conversion. 
    Returns mock text for demonstration until real libraries are installed.
    """
    # NOTE: This mock text is used for the LLM test
    mock_resume = (
        "Name: Alex Johnson. Contact: alex.j@techmail.com, +1-555-123-4567. "
        "Skills: Python, Flask, SQL, Cloud Computing. Education: M.S. in Computer Science, State University."
    )
    return mock_resume

def append_to_sheet(data_row):
    """Appends a list of values to the configured Google Sheet tab."""
    if SHEET:
        try:
            SHEET.append_row(data_row)
            return True
        except Exception as e:
            print(f"gspread Write Error: {e}")
            return False
    return False

# --- 5. FLASK WEBHOOK ROUTE ---
@app.route('/whatsapp-inbound', methods=['POST'])
def whatsapp_webhook():
    """Handles all incoming messages from Twilio's WhatsApp API."""
    from_contact = request.form.get('From', '')
    num_media = int(request.form.get('NumMedia', 0))
    
    response = MessagingResponse()
    
    if num_media > 0:
        # --- Handle Resume Attachment ---
        media_url = request.form.get('MediaUrl0')
        media_content_type = request.form.get('MediaContentType0')
        
        file_content, file_ext = download_media(media_url, media_content_type)
        
        if file_content:
            # resume_text = convert_to_text(file_content, file_ext) # COMMENTED OUT LLM CALL
            
            # HARDCODE MOCK PARSED DATA TO TEST SHEETS WRITE 
            
            # THIS BYPASSES THE QUOTA ERROR ENTIRELY
            parsed_data = {
                'name': 'Alex Johnson (MOCK)',
                'email': 'alex.j@test.com',
                'phone': '+15554567',
                'key_skills': ['Python', 'SQL', 'Twilio API'],
                'education': 'M.S. in Computer Science (MOCK)'
            }
            
            # --- BYPASS QUOTA CHECK AND PROCEED TO WRITE ---
            if parsed_data:
                # 3. Store Data in Google Sheet
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                row = [
                    timestamp,
                    from_contact,
                    parsed_data.get('name', 'N/A'),
                    parsed_data.get('email', 'N/A'),
                    parsed_data.get('phone', 'N/A'),
                    ', '.join(parsed_data.get('key_skills', [])),
                    parsed_data.get('education', 'N/A'),
                    media_url
                ]
                
                if append_to_sheet(row):
                    # SUCCESS: The full Twilio -> Flask -> Sheets pipeline works.
                    reply = "🎉 SUCCESS: MOCK data written! The API quota is exhausted, but the full pipeline (Twilio -> Sheets) is working."
                else:
                    reply = "⚠️ Error: MOCK data failed to write to Google Sheet. Check console for gspread errors."
            else:
                # Should not hit this branch with mock data
                reply = "❌ Internal Logic Failed."
        else:
            reply = "❌ Error: Could not download the resume file from the provided link. Check Twilio credentials."
    else:
        # --- Handle Plain Text Message ---
        reply = "👋 Welcome to the Resume Parser! Please send your resume file (PDF or DOCX) to start the process."

    response.message(reply)
    return str(response)

# --- 6. RUN THE APPLICATION ---
if __name__ == '__main__':
    if SHEET is None:
         print("🔴 WARNING: The application started, but the Google Sheet connection failed on startup. Check permissions/ID.")
    
    app.run(debug=True)
