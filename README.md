# whatsapp-resume-parser
Automated WhatsApp Resume Parser 
�
�📄
 
Project Overview 
This project implements an end-to-end automation system that receives unstructured resume 
files (PDF, DOCX) via WhatsApp, extracts core candidate information using a Large Language 
Model (LLM), and stores the structured data in real-time into a Google Sheet database. 
This dramatically reduces manual data entry, speeds up the candidate screening process, and 
provides a centralized, clean data source for recruitment teams. 
�
�
 Features 
● WhatsApp Webhook: Listens for incoming messages and media files using the Twilio 
API. 
● Media Handling: Downloads attached resume files (PDF/DOCX) securely from the 
Twilio-provided URL. 
● LLM-Powered Parsing: Leverages OpenAI/Gemini with Pydantic Schemas to reliably 
extract structured data (Name, Email, Skills, etc.) from unstructured text. 
● Structured Storage: Appends the clean, extracted data directly to a row in a designated 
Google Sheet. 
● Real-time Response: Sends an immediate confirmation message back to the user via 
WhatsApp. 
�
�
 Technology Stack 
Component 
Messaging 
Backend 
Technology 
Twilio API for WhatsApp 
Python 3 + Flask 
Purpose 
Handles inbound messages 
and media webhooks. 
Lightweight web server to host 
the webhook endpoint. 
AI/NLP 
Data Structure 
File Conversion 
Data Storage 
Development 
OpenAI/Gemini (via 
LangChain/SDK) 
Pydantic 
pdfminer.six, python-docx 
Extracts structured data from 
resume content. 
Enforces reliable JSON output 
from the LLM. 
Converts binary resume files 
into searchable text. 
Google Sheets API (gspread) Persistent, structured storage 
for candidate details. 
ngrok 
Exposes the local Flask server 
for Twilio webhooks during 
testing. 
⚙
 Setup and Installation 
Follow these steps to set up the project locally. 
1. Prerequisites 
1. Python 3.x installed. 
2. Twilio Account: Get your Account SID and Auth Token. 
3. OpenAI/Gemini API Key: Required for the LLM parsing component. 
4. Google Service Account: 
○ Enable Google Sheets API and Google Drive API in Google Cloud Console. 
○ Create and download the Service Account JSON key file (client_secret.json) and 
place it in the project root. 
○ Share your target Google Sheet with the Service Account email address. 
5. Target Google Sheet: Create a sheet with the following header columns (matching the 
data model): Timestamp, WhatsApp Contact, Name, Email, Phone, Key Skills, Education, 
Original File Link. 
2. Install Dependencies 
# Clone the repository (if applicable) 
# git clone [repository-url] 
# cd whatsapp-resume-parser 
# Create and activate a virtual environment 
python -m venv venv 
source venv/bin/activate 
# Install required Python packages 
pip install Flask twilio requests gspread langchain openai pydantic 
pip install pdfminer.six python-docx 
3. Configuration (.env file) 
Create a file named .env in the root directory and populate it with your credentials: 
# Twilio Credentials 
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 
# LLM API Key 
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx 
# Google Sheets Configuration 
GOOGLE_SHEET_NAME="[Name of your Google Sheet]" 
4. Run the Webhook Server 
1. Start Flask: Run your main application file (e.g., app.py). 
python app.py 
# Running on [http://127.0.0.1:5000/](http://127.0.0.1:5000/) 
2. Start ngrok: Open a separate terminal window and expose your Flask server. 
ngrok http 5000 
3. Configure Twilio: Copy the https:// forwarding URL provided by ngrok (e.g., 
https://xxxxxx.ngrok.io). Navigate to your Twilio WhatsApp Sandbox Settings and paste 
this URL, appending the route, into the "When a message comes in" field:[Your ngrok 
URL]/whatsapp-inbound 
�
�
 Testing the System 
1. Join the Sandbox: Send the required code (e.g., join code-word) to your Twilio Sandbox 
number via WhatsApp. 
2. Send Resume: Send a PDF or DOCX resume file to the same WhatsApp number. 
3. Verify: 
○ Check your Flask console for logs showing the file download and LLM parsing 
process. 
○ Check your Google Sheet; a new row should be populated with the extracted data. 
○ The WhatsApp user should receive a confirmation message. 
