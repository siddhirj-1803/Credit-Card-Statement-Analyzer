# AI-Powered Credit Card Statement Analyzer

A professional full-stack web application that analyzes credit card statements using PDF parsing and AI-powered insights.

![Portfolio Project](https://img.shields.io/badge/Portfolio-Project-blue)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)
![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask)

## Features

### Core Functionality
- **PDF Upload & Parsing**: Drag-and-drop interface with support for multiple credit card issuers
- **Data Extraction**: Automatically extracts 12+ key data points from credit card statements
- **Budget Goal Setting**: Optional budget input for personalized financial recommendations
- **AI-Powered Insights**: Google Gemini API integration for actionable financial advice

### UI/UX
- **Light/Dark Mode**: Toggle between themes with localStorage persistence
- **Responsive Design**: Clean, modern interface using Tailwind CSS
- **Professional Components**: Loading states, error handling, and visual feedback
- **Interactive Elements**: "How It Works" modal explaining the technology stack

## Technology Stack

### Frontend
- React 19 with Hooks
- Vite (build tool and dev server)
- Tailwind CSS (via CDN)
- lucide-react (icons)
- Inter font

### Backend
- Python 3.11
- Flask (web framework)
- pdfplumber (PDF text extraction)
- Regular Expressions (regex parsing)
- Google Gemini API (AI insights)
- Exponential backoff retry logic

## Getting Started

### Prerequisites
- Python 3.11
- Node.js 20
- Google Gemini API key (for AI insights feature)

### Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
# Create a .env file with your Gemini API key
echo "GEMINI_API_KEY=your_api_key_here" > .env
```

### Running the Application

The application uses two workflows:

1. **Backend** (runs on port 8000):
```bash
python main.py
```

2. **Frontend** (runs on port 5000):
```bash
npm run dev
```

Access the application at `http://localhost:5000`

## How to Use

1. **Upload PDF**: Drag and drop your credit card statement PDF or click to browse
2. **Select Issuer**: Choose your card issuer from the dropdown menu
3. **Parse Statement**: Click "Parse Statement" to extract data from your PDF
4. **View Results**: Review the extracted data displayed in clean data cards
5. **Set Budget** (Optional): Enter your monthly budget goal
6. **Get Insights**: Click "Get AI Insights" for personalized financial recommendations

## Supported Credit Card Issuers

- **CFPB Sample** (Working) - Full parsing with 12+ data points
- Chase (Demo) - Placeholder data
- American Express (Demo) - Placeholder data
- Citi (Demo) - Placeholder data
- Capital One (Demo) - Placeholder data
- Discover (Demo) - Placeholder data

## Extracted Data Points

The application extracts the following information:
1. Total Balance Due
2. Payment Due Date
3. Minimum Payment Due
4. Card Last 4 Digits
5. Billing Cycle Dates
6. Previous Balance
7. Payments, Credits
8. Purchases
9. Interest Charged
10. Credit Access Line (Credit Limit)
11. Available Credit
12. Annual Percentage Rate (APR)

## API Endpoints

### POST /api/parse
Parse uploaded PDF credit card statements
- **Input**: Form data with `file` (PDF) and `issuer` (string)
- **Output**: JSON with extracted data fields

### POST /api/insights
Generate AI-powered financial insights
- **Input**: JSON with `extractedData` (object) and `budgetGoal` (string)
- **Output**: JSON with `insights` (string)

### GET /health
Health check endpoint
- **Output**: JSON with status

## Project Structure

```
.
├── main.py                 # Flask backend
├── requirements.txt        # Python dependencies
├── package.json           # Node.js dependencies
├── vite.config.js         # Vite configuration
├── index.html             # HTML entry point
├── src/
│   ├── main.jsx          # React entry point
│   └── App.jsx           # Main React component
├── replit.md             # Project documentation
└── README.md             # This file
```

## Future Enhancements

1. Support for additional credit card issuers with real parsing
2. Statement history and comparison features
3. Data visualization charts
4. PDF export for insights
5. Enhanced AI insights with spending category breakdown

## Portfolio Highlights

This project demonstrates:
- ✅ Full-stack development (React + Python/Flask)
- ✅ PDF parsing with pdfplumber and regex
- ✅ AI integration with retry logic
- ✅ Professional UI/UX with theme switching
- ✅ RESTful API design
- ✅ Comprehensive error handling
- ✅ Responsive design patterns
- ✅ State management with React Hooks
- ✅ Modern build tools (Vite)

## License

This is a portfolio project created for demonstration purposes.

## Contact

For questions or feedback about this project, please reach out through the repository.
