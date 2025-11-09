import React, { useState, useEffect } from 'react';
import { Sun, Moon, Info, Upload, Lightbulb, X, Loader } from 'lucide-react';

function App() {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('theme') || 'dark';
  });
  
  const [showModal, setShowModal] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);
  const [issuer, setIssuer] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [error, setError] = useState('');
  const [budgetGoal, setBudgetGoal] = useState('');
  const [insights, setInsights] = useState('');
  const [isInsightsLoading, setIsInsightsLoading] = useState(false);

  useEffect(() => {
    localStorage.setItem('theme', theme);
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => prevTheme === 'dark' ? 'light' : 'dark');
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Invalid file type. Please upload a PDF file.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError('');
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      if (file.type !== 'application/pdf') {
        setError('Invalid file type. Please upload a PDF file.');
        setSelectedFile(null);
        return;
      }
      setSelectedFile(file);
      setError('');
    }
  };

  const handleParse = async () => {
    if (!selectedFile || !issuer) {
      setError('Please select a file and issuer.');
      return;
    }

    setIsLoading(true);
    setError('');
    setExtractedData(null);
    setInsights('');

    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append('issuer', issuer);

    try {
      const response = await fetch('/api/parse', {
        method: 'POST',
        body: formData,
      });

      const result = await response.json();

      if (response.ok) {
        setExtractedData(result.data);
      } else {
        setError(result.error || 'Failed to parse the PDF. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleGetInsights = async () => {
    if (!extractedData) {
      setError('No data available. Please parse a statement first.');
      return;
    }

    setIsInsightsLoading(true);
    setError('');

    try {
      const response = await fetch('/api/insights', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          extractedData: extractedData,
          budgetGoal: budgetGoal,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        setInsights(result.insights);
      } else {
        setError(result.error || 'Failed to generate insights. Please try again.');
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setIsInsightsLoading(false);
    }
  };

  return (
    <div className={theme}>
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-white transition-colors duration-200 py-8 px-4">
        <div className="max-w-2xl mx-auto">
          <header className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
            <div className="flex justify-between items-center">
              <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
                Credit Card Statement Analyzer
              </h1>
              <div className="flex gap-2">
                <button
                  onClick={() => setShowModal(true)}
                  className="p-2 rounded-lg bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors"
                  aria-label="How it works"
                >
                  <Info size={20} />
                </button>
                <button
                  onClick={toggleTheme}
                  className="p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
                  aria-label="Toggle theme"
                >
                  {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
                </button>
              </div>
            </div>
          </header>

          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
            <div
              onDragOver={handleDragOver}
              onDrop={handleDrop}
              className="border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg p-8 text-center hover:border-blue-500 dark:hover:border-blue-400 transition-colors cursor-pointer"
            >
              <input
                type="file"
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <Upload className="mx-auto mb-4 text-gray-400" size={48} />
                <p className="text-gray-600 dark:text-gray-300 mb-2">
                  {selectedFile ? selectedFile.name : 'Drag and drop your PDF here or click to browse'}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  PDF files only
                </p>
              </label>
            </div>

            <div className="mt-6">
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Select Card Issuer
              </label>
              <select
                value={issuer}
                onChange={(e) => setIssuer(e.target.value)}
                className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-gray-900 dark:text-white"
              >
                <option value="">Choose an issuer...</option>
                <option value="CFPB Sample (Working)">CFPB Sample (Working)</option>
                <option value="Chase (Demo)">Chase (Demo)</option>
                <option value="American Express (Demo)">American Express (Demo)</option>
                <option value="Citi (Demo)">Citi (Demo)</option>
                <option value="Capital One (Demo)">Capital One (Demo)</option>
                <option value="Discover (Demo)">Discover (Demo)</option>
              </select>
            </div>

            <button
              onClick={handleParse}
              disabled={!selectedFile || !issuer || isLoading}
              className="w-full mt-6 px-6 py-3 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {isLoading ? (
                <>
                  <Loader className="animate-spin" size={20} />
                  Parsing...
                </>
              ) : (
                'Parse Statement'
              )}
            </button>
          </div>

          {error && (
            <div className="bg-red-100 dark:bg-red-900 border border-red-400 dark:border-red-700 text-red-700 dark:text-red-200 px-4 py-3 rounded-lg mb-6">
              {error}
            </div>
          )}

          {extractedData && (
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 mb-6">
              <h2 className="text-xl font-bold mb-4 text-gray-900 dark:text-white">
                Extracted Statement Data
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(extractedData).map(([key, value]) => (
                  <div
                    key={key}
                    className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4"
                  >
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">
                      {key}
                    </p>
                    <p className="text-lg font-semibold text-gray-900 dark:text-white">
                      {value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-6">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Budget Goal (Optional)
                </label>
                <input
                  type="number"
                  placeholder="Enter budget goal (e.g., 1000)"
                  value={budgetGoal}
                  onChange={(e) => setBudgetGoal(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-50 dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent text-gray-900 dark:text-white"
                />
              </div>

              <button
                onClick={handleGetInsights}
                disabled={isInsightsLoading}
                className="w-full mt-4 px-6 py-3 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 dark:disabled:bg-gray-600 text-white font-medium rounded-lg transition-colors disabled:cursor-not-allowed flex items-center justify-center gap-2"
              >
                {isInsightsLoading ? (
                  <>
                    <Loader className="animate-spin" size={20} />
                    Generating Insights...
                  </>
                ) : (
                  <>
                    <Lightbulb size={20} />
                    Get AI Insights
                  </>
                )}
              </button>
            </div>
          )}

          {insights && (
            <div className="bg-gradient-to-r from-purple-100 to-blue-100 dark:from-purple-900 dark:to-blue-900 rounded-xl shadow-lg p-6">
              <div className="flex items-start gap-3">
                <Lightbulb className="text-purple-600 dark:text-purple-400 mt-1 flex-shrink-0" size={24} />
                <div>
                  <h3 className="text-lg font-bold mb-2 text-gray-900 dark:text-white">
                    AI-Powered Financial Insights
                  </h3>
                  <p className="text-gray-800 dark:text-gray-200 leading-relaxed">
                    {insights}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {showModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl max-w-lg w-full p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                  How It Works
                </h2>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-1 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-700 transition-colors"
                  aria-label="Close modal"
                >
                  <X size={24} />
                </button>
              </div>
              <div className="text-gray-700 dark:text-gray-300 space-y-3">
                <p>
                  This app uses a <strong>React + Tailwind</strong> frontend and a <strong>Python + Flask</strong> backend.
                </p>
                <p>
                  The backend uses <strong>pdfplumber</strong> and <strong>Regular Expressions (regex)</strong> to parse the PDF and extract key financial data from your credit card statement.
                </p>
                <p>
                  After parsing, you can click <strong>"Get AI Insights"</strong>. This sends the extracted data to our backend, which then uses the <strong>Google Gemini API</strong> to generate helpful financial tips based on your statement.
                </p>
                <p>
                  Set a budget goal to receive personalized recommendations tailored to your spending habits!
                </p>
              </div>
              <button
                onClick={() => setShowModal(false)}
                className="w-full mt-6 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition-colors"
              >
                Got it!
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
