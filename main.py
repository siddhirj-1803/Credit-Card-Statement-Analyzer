# main.py
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

# -------------------- Helpers --------------------
def _clean_token_str(s: str) -> str:
    if s is None:
        return ""
    s = str(s).strip()
    s = re.sub(r"\b(AAN|ANN|A/\w+)\b", "", s, flags=re.IGNORECASE)
    s = s.replace("\u200b", "").replace("\xa0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.strip(" ,;:")
    return s

def _normalize_money(raw):
    if raw is None:
        return None
    s = _clean_token_str(str(raw))
    # treat parentheses as positive
    paren = re.search(r"\(([\d,\.]+)\)", s)
    if paren:
        s = paren.group(1)
    # currency detection
    rupee_present = bool(re.search(r"(₹|Rs\.?|INR)", s))
    usd_present = bool(re.search(r"(\$|USD|US\$)", s))
    # find numeric portion
    m = re.search(r"(-?\d{1,3}(?:[,0-9]*)(?:\.\d+)?|-?\d+\.\d+)", s.replace(" ", ""))
    if not m:
        return s if s else None
    num = m.group(1).replace(",", "")
    try:
        if "." in num:
            v = float(num)
            if rupee_present:
                return f"₹{v:,.2f}"
            if usd_present:
                return f"${v:,.2f}"
            return f"₹{v:,.2f}"
        else:
            v = int(num)
            if rupee_present:
                return f"₹{v:,}"
            if usd_present:
                return f"${v:,}"
            return f"₹{v:,}"
    except Exception:
        return s

def _find_all_numbers_with_pos(text):
    tokens = []
    if not text:
        return tokens
    pattern = re.compile(r"(?:₹|Rs\.?|INR|\$)?\s*-?\d{1,3}(?:[,\d]{0,})?(?:\.\d+)?", re.IGNORECASE)
    for m in pattern.finditer(text):
        raw = m.group(0)
        norm = _normalize_money(raw)
        tokens.append((m.start(), m.end(), raw, norm))
    pattern2 = re.compile(r"\b\d{4,}\b")
    for m in pattern2.finditer(text):
        raw = m.group(0)
        if not any(abs(m.start()-t[0]) < 2 for t in tokens):
            norm = _normalize_money(raw)
            tokens.append((m.start(), m.end(), raw, norm))
    tokens.sort(key=lambda x: x[0])
    return tokens

def _find_date_in_line(text):
    if not text:
        return None
    m = re.search(r"(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4})", text)
    if m:
        return m.group(1)
    m = re.search(r"([A-Za-z]{3,9}\s+\d{1,2},\s*\d{4})", text)
    if m:
        return m.group(1)
    return None

def _closest_number_to_label(text, label_regexes, tokens):
    label_pos = None
    for rg in label_regexes:
        m = re.search(rg, text, re.IGNORECASE)
        if m:
            label_pos = m.start()
            break
    if label_pos is None:
        return None
    newline_before = text.rfind("\n", 0, label_pos)
    newline_after = text.find("\n", label_pos)
    if newline_after == -1:
        newline_after = len(text)
    same_line_tokens = [t for t in tokens if t[0] >= newline_before and t[1] <= newline_after]
    if same_line_tokens:
        same_line_tokens.sort(key=lambda t: abs((t[0]+t[1])//2 - label_pos))
        return same_line_tokens[0][3]
    if tokens:
        tokens.sort(key=lambda t: abs((t[0]+t[1])//2 - label_pos))
        return tokens[0][3]
    return None

# ---------------- debug line map helper ----------------
def _build_line_map(text):
    """
    Return a list of dicts: {index, line, numbers_found}
    and also write a debug file debug_line_map.txt for quick inspection.
    """
    lines = [ln.rstrip() for ln in text.splitlines()]
    line_map = []
    pattern = re.compile(r"(?:₹|Rs\.?|INR|\$)?\s*-?\d{1,3}(?:[,\d]{0,})?(?:\.\d+)?", re.IGNORECASE)
    debug_lines = []
    for i, ln in enumerate(lines):
        if not ln.strip():
            continue
        nums = pattern.findall(ln)
        if nums:
            entry = {"index": i, "line": ln, "numbers": nums}
            line_map.append(entry)
            debug_lines.append(f"{i:03d}: {ln}")
            debug_lines.append(f"      → {nums}")
    # write to file so you can open it even if console doesn't show prints
    try:
        debug_path = os.path.join(os.getcwd(), "debug_line_map.txt")
        with open(debug_path, "w", encoding="utf-8") as f:
            f.write("\n".join(debug_lines))
    except Exception as e:
        print(f"[DEBUG] Could not write debug_line_map.txt: {e}")
    return line_map

# ---------------- parse_improved (final) ----------------
def parse_improved(text):
    """
    Enhanced parser tuned for HDFC-style extracted text:
    - handles parentheses/negative formatting,
    - finds Payment Due Date in following lines,
    - maps Account Summary row (column mapping tuned),
    - line-aware extraction and safe fallbacks.
    """
    fields = {
        "Total Balance Due": None,
        "Payment Due Date": None,
        "Minimum Payment Due": None,
        "Card Last 4 Digits": None,
        "Billing Cycle Dates": None,
        "Previous Balance": None,
        "Payments, Credits": None,
        "Purchases": None,
        "Interest Charged": None,
        "Credit Access Line": None,
        "Available Credit": None,
        "Annual Percentage Rate": None
    }

    if not text:
        return {k: "N/A" for k in fields}

    t = text.replace('\u200b', ' ').replace('\xa0', ' ')
    lines = [ln.strip() for ln in t.splitlines() if ln.strip() != ""]

    def _clean_numeric_token(tok):
        if tok is None:
            return None
        s = str(tok)
        s = re.sub(r"[^\d\.\,\-\(\)₹Rs\$]", "", s)
        m_paren = re.search(r"\(([\d,\.]+)\)", s)
        if m_paren:
            return _normalize_money(m_paren.group(1))
        s = s.strip(" ,")
        s = re.sub(r"^-+", "", s)
        try:
            normalized = _normalize_money(s)
            return normalized
        except:
            return s

    all_tokens = _find_all_numbers_with_pos(t)
    dedup_tokens = []
    seen = set()
    for _, _, raw, norm in all_tokens:
        if norm and norm not in seen:
            cleaned = _clean_numeric_token(norm)
            if cleaned and cleaned not in seen:
                dedup_tokens.append(cleaned)
                seen.add(cleaned)

    used = set()

    # Card last 4 digits (prefer lines with 'card' etc)
    card_last4 = None
    for i, ln in enumerate(lines):
        if re.search(r"\b(card|card no|card number|account number|ending in|ending)\b", ln, re.IGNORECASE):
            m4 = re.findall(r"(\d{4})\b", ln)
            if m4:
                card_last4 = m4[-1]
                break
    if not card_last4:
        all4 = re.findall(r"\b(\d{4})\b", t)
        if all4:
            filtered = [g for g in all4 if not (1900 <= int(g) <= 2099)]
            card_last4 = filtered[-1] if filtered else all4[-1]
    if card_last4:
        fields["Card Last 4 Digits"] = card_last4

    # Billing cycle / statement date
    for i, ln in enumerate(lines):
        if re.search(r"(Statement Date|Statement Period|Billing Cycle)", ln, re.IGNORECASE):
            d = re.findall(r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}", ln)
            if d:
                fields["Billing Cycle Dates"] = f"{d[0]}" if len(d)==1 else f"{d[0]} - {d[1]}"
            else:
                if i+1 < len(lines):
                    d2 = re.findall(r"\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2,4}", lines[i+1])
                    if d2:
                        fields["Billing Cycle Dates"] = d2[0]
            break

    # Payment Due Date (search header then next lines)
    for i, ln in enumerate(lines):
        if re.search(r"Payment\s*Due\s*Date", ln, re.IGNORECASE):
            dt = _find_date_in_line(ln)
            if dt:
                fields["Payment Due Date"] = dt
            else:
                for j in range(i+1, min(i+4, len(lines))):
                    dt2 = _find_date_in_line(lines[j])
                    if dt2:
                        fields["Payment Due Date"] = dt2
                        break
            break
    if fields["Payment Due Date"] is None:
        for i, ln in enumerate(lines):
            if re.search(r"(Total\s+Dues|Minimum\s+Payment|Minimum\s+Amount)", ln, re.IGNORECASE):
                for j in range(i, min(i+4, len(lines))):
                    dt3 = _find_date_in_line(lines[j])
                    if dt3:
                        fields["Payment Due Date"] = dt3
                        break
            if fields["Payment Due Date"]:
                break

    # Account Summary row detection
    for i, ln in enumerate(lines):
        if re.search(r"Account\s+Summary", ln, re.IGNORECASE) or re.search(r"Opening\s+Payment\/\s*Purchase\/\s*Finance", ln, re.IGNORECASE) or re.search(r"Opening\s+Balance.*Payments.*Purchase", ln, re.IGNORECASE):
            numeric_row = None
            for j in range(i+1, min(i+6, len(lines))):
                nums = re.findall(r"(?:₹|Rs\.?|INR|\$)?\s*-?\d{1,3}(?:[,\d]{0,})?(?:\.\d+)?", lines[j])
                if len(nums) >= 3:
                    numeric_row = nums
                    row_line_idx = j
                    break
            if numeric_row:
                cleaned_nums = [_clean_numeric_token(n) for n in numeric_row]
                while len(cleaned_nums) < 5:
                    cleaned_nums.append(None)
                # Based on your sample this mapping works better:
                # Opening Balance | Finance Charges | Purchases | Payments/Credits | Total Dues
                mapping = [
                    ("Previous Balance", cleaned_nums[0]),
                    ("Interest Charged", cleaned_nums[1]),
                    ("Purchases", cleaned_nums[2]),
                    ("Payments, Credits", cleaned_nums[3]),
                    ("Total Balance Due", cleaned_nums[4])
                ]
                for key, val in mapping:
                    if val and val != "N/A" and val not in used:
                        fields[key] = val
                        used.add(val)
                # Detect Available Credit nearby
                if fields["Available Credit"] in [None, "N/A"]:
                    m = re.search(r"Available\s+(?:Credit|Credit\s+Limit)[:\s]*₹?\s*([\d,\.]+)", t, re.IGNORECASE)
                    if m:
                        fields["Available Credit"] = _clean_numeric_token(m.group(1))
                break

    # If Total Balance Due still missing, search Total Dues lines
    if fields["Total Balance Due"] is None:
        for i, ln in enumerate(lines):
            if re.search(r"(Total\s+Dues|Total\s+Amount\s+Due|Amount\s+Payable|Outstanding\s+Balance)", ln, re.IGNORECASE):
                nums = re.findall(r"(?:₹|Rs\.?|INR|\$)?\s*-?\d{1,3}(?:[,\d]{0,})?(?:\.\d+)?", ln)
                if nums:
                    val = _clean_numeric_token(nums[-1])
                    if val and val not in used:
                        fields["Total Balance Due"] = val
                        used.add(val)
                        break
                if i+1 < len(lines):
                    nums2 = re.findall(r"(?:₹|Rs\.?|INR|\$)?\s*-?\d{1,3}(?:[,\d]{0,})?(?:\.\d+)?", lines[i+1])
                    if nums2:
                        val2 = _clean_numeric_token(nums2[-1])
                        if val2 and val2 not in used:
                            fields["Total Balance Due"] = val2
                            used.add(val2)
                            break
    # fallback for Total Balance Due general pattern
    if fields["Total Balance Due"] in [None, "N/A"]:
        m = re.search(r"(?:Total\s+Dues|Total\s+Amount\s+Due|Outstanding\s+Amount|Amount\s+Payable)[:\s]*₹?\s*([\d,\,\.]+)", t, re.IGNORECASE)
        if m:
            fields["Total Balance Due"] = _clean_numeric_token(m.group(1))

    # Fallback for Payments,Credit explicit matches
    if fields["Payments, Credits"] in [None, "N/A"]:
        m = re.search(r"Payments[,\s]+Credits[:\s]*₹?\s*([\d,\,\.]+)", t, re.IGNORECASE)
        if not m:
            m = re.search(r"Payments\s*[:\s]*₹?\s*([\d,\,\.]+)", t, re.IGNORECASE)
        if m:
            fields["Payments, Credits"] = _clean_numeric_token(m.group(1))

    # Try to fill some other fields by label proximity
    label_map = {
        "Credit Access Line": [r"Credit\s+Limit", r"Credit\s+Access\s+Line", r"Credit\s+Line"],
        "Available Credit": [r"Available\s+Credit", r"Available\s+Limit", r"Available\s+Credit\s+Limit"],
        "Minimum Payment Due": [r"Minimum\s+(?:Payment|Amount)\s+Due", r"\bMin\s+Payment\b"],
        "Interest Charged": [r"Interest\s+Charged", r"Finance\s+Charges?", r"\bInterest\b"],
        "Purchases": [r"\bPurchases\b", r"Purchase\s*\/\s*Debits"],
        "Previous Balance": [r"Previous\s+Balance", r"Opening\s+Balance"],
    }

    tokens_pos = _find_all_numbers_with_pos(t)
    for field_name, regexes in label_map.items():
        if fields.get(field_name) is not None and fields[field_name] != "N/A":
            continue
        val = _closest_number_to_label(t, regexes, tokens_pos)
        if val:
            cleaned = _clean_numeric_token(val)
            if cleaned and cleaned not in used:
                fields[field_name] = cleaned
                used.add(cleaned)

    # Minimum Payment Due specific attempt
    if fields["Minimum Payment Due"] in [None, "N/A"]:
        m_min = re.search(r"Minimum\s+(?:Amount|Payment)\s+Due[:\s]*₹?\s*([\d,\,\.]+)", t, re.IGNORECASE)
        if not m_min:
            header_idx = t.find("Minimum Amount Due")
            if header_idx != -1:
                snippet = t[header_idx:header_idx+120]
                m2 = re.search(r"₹?\s*([\d,\,\.]+)", snippet)
                if m2:
                    m_min = m2
        if m_min:
            fields["Minimum Payment Due"] = _clean_numeric_token(m_min.group(1))

    # Final sanitization and clamp unrealistic numbers
    for k in list(fields.keys()):
        v = fields[k]
        if v is None or str(v).strip() == "":
            fields[k] = "N/A"
            continue
        s = str(v).strip()
        # Accept zero for certain fields
        if s in [",", ".", "-", "₹0", "₹0.00", "0", "0.00"]:
            if k == "Minimum Payment Due":
                fields[k] = "₹0"
            else:
                if k in ["Purchases", "Minimum Payment Due", "Interest Charged"]:
                    fields[k] = s if re.search(r"\d", s) else ("₹0.00" if k in ["Purchases", "Interest Charged"] else "N/A")
                else:
                    fields[k] = "N/A"
            continue
        numstr = re.sub(r"[^\d\.]", "", s)
        try:
            if numstr != "":
                valf = float(numstr)
                if valf < 0 or valf > 10_000_000:
                    fields[k] = "N/A"
                    continue
        except:
            pass
        if re.fullmatch(r"[A-Za-z]", s):
            fields[k] = "N/A"
            continue
        fields[k] = s

    return fields

# -------------------- API endpoints --------------------
@app.route('/api/parse', methods=['POST'])
def parse_pdf():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400

        file = request.files['file']
        issuer = request.form.get('issuer', 'AUTO')

        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if not file.filename.lower().endswith('.pdf'):
            return jsonify({"error": "Invalid file type. Please upload a PDF file."}), 400

        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)

        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                try:
                    ptext = page.extract_text() or ""
                    ptext = ptext.replace('\u200b', ' ').replace('\xa0', ' ')
                    text += ptext + "\n"
                except Exception:
                    continue

        # DEBUG: save extracted text for inspection
        debug_path = os.path.join(os.getcwd(), "debug_extracted_text.txt")
        try:
            with open(debug_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[DEBUG] Extracted text saved to: {debug_path}")
        except Exception as e:
            print(f"[DEBUG ERROR] Could not write debug file: {e}")

        # also write line map debug (useful when console doesn't show)
        try:
            _build_line_map(text)
        except Exception:
            pass

        if not text.strip():
            return jsonify({"error": "Could not extract text from PDF. If this is scanned image PDF, enable OCR."}), 400

        parsed = parse_improved(text)

        return jsonify({"data": parsed, "raw_sample": text[:6000]}), 200

    except Exception as e:
        return jsonify({"error": f"An error occurred while parsing the PDF: {str(e)}"}), 500

@app.route('/debug-text', methods=['POST'])
def debug_text():
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)
        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        if not text.strip():
            return jsonify({"error": "No text extracted; PDF may be scanned (image)."}), 400
        return jsonify({"text_sample": text[:20000]}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/debug_lines', methods=['POST'])
def debug_lines():
    """
    Upload same PDF to get a JSON mapping of lines -> numbers found.
    Use this to see exactly where numbers live in the extracted text.
    """
    try:
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files['file']
        pdf_bytes = file.read()
        pdf_file = io.BytesIO(pdf_bytes)

        text = ""
        with pdfplumber.open(pdf_file) as pdf:
            for page in pdf.pages:
                try:
                    ptext = page.extract_text() or ""
                    ptext = ptext.replace('\u200b', ' ').replace('\xa0', ' ')
                    text += ptext + "\n"
                except Exception:
                    continue

        if not text.strip():
            return jsonify({"error": "No text extracted. PDF may be scanned (image)."}), 400

        line_map = _build_line_map(text)
        # Also return beginning of raw text for context
        return jsonify({"line_map": line_map, "raw_sample": text[:8000]}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------- Insights (Gemini) --------------------
def generate_insights_with_retry(parsed_data, budget_goal, max_retries=3):
    api_key = os.getenv("GEMINI_API_KEY", "")
    if not api_key:
        return "GEMINI_API_KEY not set."
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    system_prompt = "You are a helpful assistant. Provide 2-3 short insights based on the parsed statement data only."
    user_query = f"Statement summary: {json.dumps(parsed_data)}. Budget: {budget_goal}"
    payload = {"system_instruction": {"parts": [{"text": system_prompt}]}, "contents": [{"parts": [{"text": user_query}]}]}
    for attempt in range(max_retries):
        try:
            r = requests.post(api_url, json=payload, headers={"Content-Type": "application/json"}, timeout=15)
            if r.status_code == 200:
                res = r.json()
                try:
                    return res["candidates"][0]["content"]["parts"][0]["text"]
                except:
                    return "No candidate content."
            elif r.status_code >= 500 or r.status_code == 429:
                time.sleep((2 ** attempt))
                continue
            else:
                return f"API error {r.status_code}"
        except Exception:
            time.sleep((2 ** attempt))
            continue
    return "Failed to generate insights."

@app.route('/api/insights', methods=['POST'])
def get_insights():
    try:
        data = request.json
        parsed_data = data.get('extractedData')
        budget_goal = data.get('budgetGoal', '')
        if not parsed_data:
            return jsonify({"error": "No extracted data provided"}), 400
        text = generate_insights_with_retry(parsed_data, budget_goal)
        return jsonify({"insights": text}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)), debug=True)
