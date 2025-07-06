from flask import Flask, render_template, request, send_file
import pandas as pd
from datetime import datetime
import os

app = Flask(__name__)

QUARTER_RANGES = {
    "Q1": ("2024-07-01", "2024-09-30"),
    "Q2": ("2024-10-01", "2024-12-31"),
    "Q3": ("2025-01-01", "2025-03-31"),
    "Q4": ("2025-04-01", "2025-06-30"),
}

CSV_COLUMNS = [
    "Constituency", "Quarter", "Opening_Balance",
    "Closing_Balance", "Transfer_to_Main",
    "Transfer_Date", "Adjusted_Difference", "Status"
]

diagnosis_results = []

def is_transfer_date_valid(quarter_key, transfer_date_str):
    if not transfer_date_str:
        return True
    try:
        transfer_date = datetime.strptime(transfer_date_str, "%Y-%m-%d").date()
        start_date = datetime.strptime(QUARTER_RANGES[quarter_key][0], "%Y-%m-%d").date()
        end_date = datetime.strptime(QUARTER_RANGES[quarter_key][1], "%Y-%m-%d").date()
        return start_date <= transfer_date <= end_date
    except Exception:
        return False

def diagnose(opening_balance, closing_balance, transfer_to_main,
             constituency, quarter_key, transfer_date_str, threshold=-100_000):

    # Input validation: If invalid, return None + error
    if quarter_key not in QUARTER_RANGES:
        return None, "❌ Invalid Quarter. Please enter Q1, Q2, Q3, or Q4."

    if not is_transfer_date_valid(quarter_key, transfer_date_str):
        return None, "❌ Invalid Transfer Date. It must lie within the selected quarter."

    adjusted_difference = (closing_balance - opening_balance) + transfer_to_main

    if transfer_to_main == 0 and closing_balance > opening_balance:
        status = "OK – Increase due to loan repayments by groups and institution"
    elif adjusted_difference >= threshold:
        status = "OK – Within acceptable threshold"
    else:
        status = "AUDIT NEEDED – Excessive drop"

    result = {
        "Constituency": constituency,
        "Quarter": quarter_key,
        "Opening_Balance": opening_balance,
        "Closing_Balance": closing_balance,
        "Transfer_to_Main": transfer_to_main,
        "Transfer_Date": transfer_date_str or "N/A",
        "Adjusted_Difference": adjusted_difference,
        "Status": status
    }

    diagnosis_results.append(result)
    df = pd.DataFrame(diagnosis_results)

    os.makedirs('results', exist_ok=True)
    df[CSV_COLUMNS].to_csv('results/diagnosis.csv', index=False)
    df[CSV_COLUMNS].to_excel('results/diagnosis.xlsx', index=False)

    return result, None

@app.route('/', methods=['GET', 'POST'])
def index():
    error = None
    if request.method == 'POST':
        constituency = request.form['constituency']
        quarter = request.form['quarter'].strip().upper()
        opening = float(request.form['opening_balance'])
        closing = float(request.form['closing_balance'])
        transfer = float(request.form['transfer_to_main'])
        transfer_date = request.form['transfer_date']

        result, error = diagnose(opening, closing, transfer, constituency, quarter, transfer_date)

        if error:
            return render_template('index.html', error=error)

        return render_template('result.html', result=result)

    return render_template('index.html')

@app.route('/download/<filetype>')
def download(filetype):
    if filetype == 'csv':
        path = 'results/diagnosis.csv'
    elif filetype == 'excel':
        path = 'results/diagnosis.xlsx'
    else:
        return "Unsupported format", 400

    return send_file(path, as_attachment=True)

if __name__ == '__main__':
    app.run(host="0.0.0.0",port=5000,debug=True)

