import numpy as np
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, session, json
import pandas as pd
import calendar
import datetime
from werkzeug.utils import secure_filename
import csv
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

class Expense:
    def __init__(self, name, category, amount, date):
        self.name = name
        self.category = category
        self.amount = amount
        self.date = date

class Bank_Transaction:
    def __init__(self, date, name, amount, balance):
        self.date = date
        self.name = name
        self.amount = amount
        self.balance = balance

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_expense', methods=['POST'])
def add_expense():
    expense_name = request.form['expense_name']
    expense_amount = float(request.form['expense_amount'])
    expense_category = request.form['expense_category']
    expense_date = datetime.datetime.strptime(request.form['expense_date'], '%Y-%m-%d').date()

    new_expense = Expense(name=expense_name, category=expense_category, amount=expense_amount, date=expense_date)
    save_expense_to_file(new_expense)

    return redirect(url_for('index'))

@app.route('/summary')
def summary():
    expenses = load_expenses_from_file()
    summary_data = summarize_expenses(expenses, 2000)
    return render_template('summary.html', summary_data=summary_data)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    created_expenses = load_expenses_from_file()
    return render_template('expenses.html', expenses=created_expenses)


@app.route('/bank_transactions', methods=['GET', 'POST'])
def bank_transactions():
    # Retrieve uploaded_transactions from the session if it exists
    uploaded_transactions_json = session.get('uploaded_transactions', '[]')
    uploaded_transactions = pd.read_json(uploaded_transactions_json)

    if request.method == 'POST':
        # Handle file upload
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['file']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            flash('File uploaded successfully')

            # Update uploaded_transactions and store it in the session as JSON
            uploaded_transactions = df_cleaning(pd.read_csv(file_path, sep=';'))
            uploaded_transactions_json = uploaded_transactions.to_json(orient='records')
            session['uploaded_transactions'] = uploaded_transactions_json

    return render_template('bank_transactions.html',
                           uploaded_transactions=uploaded_transactions.to_dict(orient='records'))


def save_expense_to_file(expense):
    with open("expenses.csv", "a") as f:
        f.write(f"{expense.name},{expense.amount},{expense.category},{expense.date}\n")


def load_expenses_from_file(filename="expenses.csv"):
    expenses = []
    with open(filename, "r") as f:
        lines = f.readlines()
        for line in lines:
            stripped_line = line.strip()
            elements = stripped_line.split(",")
            if len(elements) == 4:
                expense_name, expense_amount, expense_category, expense_date_str = elements
                expense_date = datetime.datetime.strptime(expense_date_str, '%Y-%m-%d').date()
                formatted_date = expense_date.strftime('%Y-%m-%d')

                line_expense = Expense(
                    name=expense_name,
                    amount=float(expense_amount),
                    category=expense_category,
                    date=formatted_date
                )
                expenses.append(line_expense)
    return expenses

def df_cleaning(df):
    df = df[['Datum', 'Naam / Omschrijving', 'Af Bij', 'Bedrag (EUR)', 'Saldo na mutatie']]
    df.rename(columns={'Naam / Omschrijving': 'Naam'}, inplace=True)
    df['Bedrag (EUR)'] = df['Bedrag (EUR)'].str.replace(',', '.').astype(float)
    df['Saldo na mutatie'] = df['Saldo na mutatie'].str.replace(',', '.').astype(float)
    df.loc[df['Af Bij'] == 'Af', 'Bedrag (EUR)'] = -abs(df['Bedrag (EUR)'])
    df.drop('Af Bij', axis=1, inplace=True)
    df['Datum'] = pd.to_datetime(df['Datum'], format='%Y%m%d').dt.date

    return df

# Test commit

def summarize_expenses(expenses, budget):
    amount_by_category = {}
    for expense in expenses:
        key = expense.category
        if key in amount_by_category:
            amount_by_category[key] += expense.amount
        else:
            amount_by_category[key] = expense.amount

    total_spent = sum([ex.amount for ex in expenses])

    remaining_budget = budget - total_spent

    now = datetime.datetime.now()
    days_in_month = calendar.monthrange(now.year, now.month)[1]
    remaining_days = days_in_month - now.day

    daily_budget = remaining_budget / remaining_days

    return {
        'amount_by_category': amount_by_category,
        'budget': budget,
        'total_spent': total_spent,
        'remaining_budget': remaining_budget,
        'remaining_days': remaining_days,
        'daily_budget': daily_budget
    }

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.run(debug=True)
