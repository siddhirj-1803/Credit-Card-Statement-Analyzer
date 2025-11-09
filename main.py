from flask import Flask, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
import io
import requests
import time
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

def parse_cfpb_sample(text):
    """
    Parse CFPB sample credit card statement.
    Extracts 12+ key data points using comprehensive regex patterns.
    """
    data = {
        "Total Balance Due": "N/A",
        "Payment Due Date": "N/A",
        "Minimum Payment Due": "N/A",
        "Card Last 4 Digits": "N/A",
        "Billing Cycle Dates": "N/A",
        "Previous Balance": "N/A",
        "Payments, Credits": "N/A",
        "Purchases": "N/A",
        "Interest Charged": "N/A",
        "Credit Access Line": "N/A",
        "Available Credit": "N/A",
        "Annual Percentage Rate": "N/A"
    }
    
    try:
        new_balance_pattern = r"New Balance[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(new_balance_pattern, text, re.IGNORECASE)
        if match:
            data["Total Balance Due"] = f"${match.group(1)}"
        
        payment_due_pattern = r"Payment Due Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})"
        match = re.search(payment_due_pattern, text, re.IGNORECASE)
        if match:
            data["Payment Due Date"] = match.group(1)
        
        min_payment_pattern = r"Minimum Payment Due[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(min_payment_pattern, text, re.IGNORECASE)
        if match:
            data["Minimum Payment Due"] = f"${match.group(1)}"
        
        account_pattern = r"Account Number[:\s]*.*?(\d{4})"
        match = re.search(account_pattern, text, re.IGNORECASE)
        if match:
            data["Card Last 4 Digits"] = match.group(1)
        
        billing_cycle_pattern = r"(?:Opening|Closing).*?Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4}).*?(\d{1,2}/\d{1,2}/\d{2,4})"
        match = re.search(billing_cycle_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data["Billing Cycle Dates"] = f"{match.group(1)} - {match.group(2)}"
        
        prev_balance_pattern = r"Previous Balance[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(prev_balance_pattern, text, re.IGNORECASE)
        if match:
            data["Previous Balance"] = f"${match.group(1)}"
        
        payments_pattern = r"Payments,?\s*Credits?[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(payments_pattern, text, re.IGNORECASE)
        if match:
            data["Payments, Credits"] = f"${match.group(1)}"
        
        purchases_pattern = r"Purchases[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(purchases_pattern, text, re.IGNORECASE)
        if match:
            data["Purchases"] = f"${match.group(1)}"
        
        interest_pattern = r"Interest Charged[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(interest_pattern, text, re.IGNORECASE)
        if match:
            data["Interest Charged"] = f"${match.group(1)}"
        
        credit_limit_pattern = r"Credit (?:Access )?Line[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(credit_limit_pattern, text, re.IGNORECASE)
        if match:
            data["Credit Access Line"] = f"${match.group(1)}"
        
        available_credit_pattern = r"Available Credit[:\s]*\$?([\d,]+\.?\d*)"
        match = re.search(available_credit_pattern, text, re.IGNORECASE)
        if match:
            data["Available Credit"] = f"${match.group(1)}"
        
        apr_pattern = r"Annual Percentage Rate.*?Purchase.*?([\d.]+)%"
        match = re.search(apr_pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            data["Annual Percentage Rate"] = f"{match.group(1)}%"
    
    except Exception as e:
        print(f"Error parsing CFPB sample: {str(e)}")
    
    return data

def parse_chase(text):
    """Demo function for Chase statements - returns placeholder data"""
    return {
        "Total Balance Due": "N/A (Demo)",
        "Payment Due Date": "N/A (Demo)",
        "Minimum Payment Due": "N/A (Demo)",
        "Card Last 4 Digits": "N/A (Demo)",
        "Billing Cycle Dates": "N/A (Demo)",
        "Previous Balance": "N/A (Demo)",
        "Payments, Credits": "N/A (Demo)",
        "Purchases": "N/A (Demo)",
        "Interest Charged": "N/A (Demo)",
        "Credit Access Line": "N/A (Demo)",
        "Available Credit": "N/A (Demo)",
        "Annual Percentage Rate": "N/A (Demo)"
    }

def parse_amex(text):
    """Demo function for American Express statements - returns placeholder data"""
    return parse_chase(text)

def parse_citi(text):
    """Demo function for Citi statements - returns placeholder data"""
    return parse_chase(text)

def parse_capital_one(text):
    """Demo function for Capital One statements - returns placeholder data"""
    return parse_chase(text)

def parse_discover(text):
    """Demo function for Discover statements - returns placeholder data"""
    return parse_chase(text)

def parse_statement(text, issuer):
    """
    Router function that directs to the appropriate parser based on issuer.
    """
    issuer_lower = issuer.lower()
    
    if "cfpb" in issuer_lower:
        return parse_cfpb_sample(text)
    elif "chase" in issuer_lower:
        return parse_chase(text)
    elif "american express" in issuer_lower or "amex" in issuer_lower:
        return parse_amex(text)
    elif "citi" in issuer_lower:
        return parse_citi(text)
    elif "capital one" in issuer_lower:
        return parse_capital_one(text)
    elif "discover" in issuer_lower:
        return parse_discover(text)
    else:
        return parse_cfpb_sample(text)

@app.route('/api/parse', methods=['POST'])
def parse_pdf():
    """
    Endpoint to parse uploaded PDF credit card statements.
    Accepts a PDF file and issuer name, returns extracted data.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        issuer = request.form.get('issuer', 'CFPB Sample')
        
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not file.filename or not file.filename.endswith('.pdf'):
            return jsonify({"error": "Invalid file type. Please upload a PDF file."}), 400
        
        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
        
        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF. Please ensure it's a text-based PDF."}), 400
        
        parsed_data = parse_statement(text, issuer)
        
        return jsonify({"data": parsed_data}), 200
    
    except Exception as e:
        return jsonify({"error": f"An error occurred while parsing the PDF: {str(e)}"}), 500

def generate_insights_with_retry(parsed_data, budget_goal, max_retries=5):
    """
    Generate AI insights using Google Gemini API with exponential backoff retry logic.
    
    Args:
        parsed_data: Dictionary containing extracted statement data
        budget_goal: User's monthly budget goal (string)
        max_retries: Maximum number of retry attempts
    
    Returns:
        String containing AI-generated insights
    """
    api_key = os.getenv("GEMINI_API_KEY", "")
    
    if not api_key:
        return "API key not configured. Please set the GEMINI_API_KEY environment variable."
    
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    budget_context = "The user has not set a budget goal."
    if budget_goal and budget_goal.strip():
        try:
            float(budget_goal)
            budget_context = f"The user has set a monthly budget goal of ${budget_goal}. Please use this to personalize your advice."
        except ValueError:
            pass
    
    system_prompt = f"You are a friendly financial assistant. A user has provided a *comprehensive summary* from their credit card statement (including balance, purchases, payments, and credit limit). {budget_context} Your task is to provide 2-3 brief, actionable, and encouraging insights based *only* on this data. Do not invent data. Format your response as a simple text paragraph. Be encouraging."
    
    user_query = f"Here is my complete statement summary: {json.dumps(parsed_data)}. What are your insights?"
    
    payload = {
        "system_instruction": {
            "parts": [{"text": system_prompt}]
        },
        "contents": [
            {
                "parts": [{"text": user_query}]
            }
        ]
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                api_url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if "candidates" in result and len(result["candidates"]) > 0:
                    if "content" in result["candidates"][0]:
                        if "parts" in result["candidates"][0]["content"]:
                            return result["candidates"][0]["content"]["parts"][0]["text"]
                return "Unable to generate insights. Please try again."
            
            elif response.status_code == 429 or response.status_code >= 500:
                if attempt < max_retries - 1:
                    wait_time = (2 ** attempt) + (time.time() % 1)
                    print(f"Rate limited or server error. Retrying in {wait_time:.2f} seconds...")
                    time.sleep(wait_time)
                    continue
                else:
                    return "API rate limit exceeded. Please try again in a moment."
            
            else:
                return f"API Error: {response.status_code}. Please check your API key and try again."
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt)
                print(f"Request timeout. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            else:
                return "Request timeout. Please try again."
        
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt)
                time.sleep(wait_time)
                continue
            else:
                return f"Error generating insights: {str(e)}"
    
    return "Unable to generate insights after multiple attempts. Please try again later."

@app.route('/api/insights', methods=['POST'])
def get_insights():
    """
    Endpoint to generate AI-powered financial insights.
    Accepts extracted data and budget goal, returns personalized recommendations.
    """
    try:
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        parsed_data = data.get('extractedData')
        budget_goal = data.get('budgetGoal', '')
        
        if not parsed_data:
            return jsonify({"error": "No extracted data provided"}), 400
        
        insights_text = generate_insights_with_retry(parsed_data, budget_goal)
        
        return jsonify({"insights": insights_text}), 200
    
    except Exception as e:
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
