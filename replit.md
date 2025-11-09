# AI-Powered Credit Card Statement Analyzer

## Overview
A professional full-stack web application that analyzes credit card statements using PDF parsing and AI-powered insights. Built with React (frontend) and Flask (backend), this application demonstrates modern web development practices, including responsive design, theme switching, and API integration.

## Purpose
This portfolio project showcases:
- Full-stack development capabilities (React + Python/Flask)
- PDF parsing using pdfplumber and regex
- AI integration with Google Gemini API
- Professional UI/UX with light/dark mode
- RESTful API design with proper error handling
- Responsive design with Tailwind CSS

## Technology Stack

### Frontend
- **React 19** with Hooks for state management
- **Vite** as build tool and dev server
- **Tailwind CSS** (CDN) for styling with dark mode support
- **lucide-react** for icons
- **Inter font** from Google Fonts

### Backend
- **Python 3.11**
- **Flask** web framework with CORS support
- **pdfplumber** for PDF text extraction
- **Regular Expressions (regex)** for data parsing
- **Google Gemini API** for AI-powered financial insights
- **Exponential backoff retry logic** for API reliability

## Features

### Core Functionality
1. **PDF Upload & Parsing**
   - Drag-and-drop file upload interface
   - Supports multiple credit card issuers (CFPB Sample working, others demo)
   - Extracts 12+ key data points from statements

2. **Data Extraction**
   - Total Balance Due
   - Payment Due Date
   - Minimum Payment Due
   - Card Last 4 Digits
   - Billing Cycle Dates
   - Previous Balance
   - Payments, Credits
   - Purchases
   - Interest Charged
   - Credit Access Line (Credit Limit)
   - Available Credit
   - Annual Percentage Rate (APR)

3. **Budget Goal Feature**
   - Optional budget input field
   - Personalized AI recommendations based on budget

4. **AI-Powered Insights**
   - Google Gemini API integration
   - Budget-aware financial recommendations
   - 2-3 actionable, encouraging insights
   - Exponential backoff for API reliability

### UI/UX Features
- **Light/Dark Mode Toggle**
  - Persisted in localStorage
  - Smooth transitions
  - Theme-aware Tailwind classes

- **Professional Design**
  - Clean, modern interface
  - Responsive grid layouts
  - Loading states and spinners
  - Error handling with user-friendly messages
  - Rounded corners and shadows

- **Interactive Elements**
  - "How It Works" modal explaining the technology stack
  - Drag-and-drop file upload
  - Disabled states for buttons when appropriate
  - Visual feedback for all interactions

## Project Structure
```
.
├── main.py                 # Flask backend with API endpoints
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── vite.config.js         # Vite configuration
├── index.html             # HTML entry point
├── src/
│   ├── main.jsx          # React entry point
│   └── App.jsx           # Main React component
└── replit.md             # This file
```

## API Endpoints

### POST /api/parse
Parses uploaded PDF credit card statements.
- **Input**: Form data with `file` (PDF) and `issuer` (string)
- **Output**: JSON with extracted data fields
- **Error Handling**: File validation, PDF parsing errors

### POST /api/insights
Generates AI-powered financial insights.
- **Input**: JSON with `extractedData` (object) and `budgetGoal` (string)
- **Output**: JSON with `insights` (string)
- **Features**: Exponential backoff retry, timeout handling

### GET /health
Health check endpoint.
- **Output**: JSON with status

## Environment Variables
- `GEMINI_API_KEY`: Google Gemini API key (required for AI insights)

## Development Setup

### Workflows
- **Backend**: Runs on port 8000 (Flask server)
- **Frontend**: Runs on port 5000 (Vite dev server with proxy to backend)

### Running the Application
Both workflows start automatically on Replit. The frontend proxies API requests to the backend.

## PDF Parsing Details

### CFPB Sample Parser (Working)
Uses 12+ regex patterns to extract data:
1. New Balance: `r"New Balance[:\s]*\$?([\d,]+\.?\d*)"`
2. Payment Due Date: `r"Payment Due Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4})"`
3. Minimum Payment: `r"Minimum Payment Due[:\s]*\$?([\d,]+\.?\d*)"`
4. Account Number: `r"Account Number[:\s]*.*?(\d{4})"`
5. Billing Cycle: `r"(?:Opening|Closing).*?Date[:\s]*(\d{1,2}/\d{1,2}/\d{2,4}).*?(\d{1,2}/\d{1,2}/\d{2,4})"`
6. Previous Balance: `r"Previous Balance[:\s]*\$?([\d,]+\.?\d*)"`
7. Payments/Credits: `r"Payments,?\s*Credits?[:\s]*\$?([\d,]+\.?\d*)"`
8. Purchases: `r"Purchases[:\s]*\$?([\d,]+\.?\d*)"`
9. Interest Charged: `r"Interest Charged[:\s]*\$?([\d,]+\.?\d*)"`
10. Credit Limit: `r"Credit (?:Access )?Line[:\s]*\$?([\d,]+\.?\d*)"`
11. Available Credit: `r"Available Credit[:\s]*\$?([\d,]+\.?\d*)"`
12. APR: `r"Annual Percentage Rate.*?Purchase.*?([\d.]+)%"`

### Demo Parsers
Chase, American Express, Citi, Capital One, and Discover parsers return placeholder "N/A (Demo)" values.

## AI Insights Implementation

### System Prompt
Dynamically constructed based on:
- Comprehensive statement data (12+ fields)
- User's budget goal (if provided)
- Instruction to provide 2-3 brief, actionable insights

### Retry Logic
- **Max Retries**: 5 attempts
- **Exponential Backoff**: `(2 ** attempt) + random jitter`
- **Handles**: Rate limits (429), server errors (5xx), timeouts
- **Timeout**: 30 seconds per request

## Recent Changes
- **2025-11-09**: Initial implementation with all core features
  - Complete frontend with React and Tailwind CSS
  - Complete backend with Flask and pdfplumber
  - AI integration with Google Gemini API
  - Light/dark mode with localStorage persistence
  - Comprehensive error handling and loading states

## User Preferences
- Clean, professional code with comprehensive comments
- Modern UI/UX patterns
- Proper error handling throughout
- Portfolio-ready implementation quality

## Next Steps (Future Enhancements)
1. Add support for additional credit card issuers with real parsing
2. Implement statement history and comparison features
3. Add data visualization charts
4. Create PDF export for insights
5. Enhanced AI insights with spending category breakdown
