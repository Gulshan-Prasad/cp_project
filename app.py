from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
from config import db_config

app = Flask(__name__)

# Function to get a connection to the database
def get_db_connection():
    return mysql.connector.connect(**db_config)

@app.route('/')
def index():
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC LIMIT 5")
                expenses = cursor.fetchall()
        return render_template('index.html', expenses=expenses)
    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
        return "Error fetching data from the database.", 500

@app.route('/expenses')
def all_expenses():
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM expenses ORDER BY created_at DESC")
                expenses = cursor.fetchall()
        return render_template('expenses.html', expenses=expenses)
    except mysql.connector.Error as e:
        print(f"Error fetching data: {e}")
        return "Error fetching data from the database.", 500

@app.route('/add', methods=['POST'])
def add_expense():
    try:
        title = request.form['title']
        amount = request.form['amount']
        date = request.form['date']
        category = request.form['category']
        description = request.form.get('description', '')  # Use empty string if not provided

        # Validate required fields
        if not title or not amount or not date or not category:
            return "All fields are required", 400

        # Validate amount to ensure it's a valid decimal
        try:
            amount = float(amount)  # Ensure amount is a float
        except ValueError:
            return "Invalid amount provided", 400

        # Validate date format if necessary (you can expand on this)
        if not date:
            return "Date is required", 400

        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "INSERT INTO expenses (title, amount, date, category, description) VALUES (%s, %s, %s, %s, %s)",
                    (title, amount, date, category, description)
                )
            conn.commit()

        return redirect(url_for('index'))
    except mysql.connector.Error as e:
        print(f"Error adding expense: {e}")
        return "Error adding expense to the database.", 500
    except Exception as e:
        print(f"General error: {e}")
        return f"An unexpected error occurred: {e}", 500

@app.route('/delete/<int:id>')
def delete_expense(id):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM expenses WHERE id = %s", (id,))
            conn.commit()
        return redirect(url_for('all_expenses'))
    except mysql.connector.Error as e:
        print(f"Error deleting expense: {e}")
        return "Error deleting expense from the database.", 500

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if request.method == 'GET':
            # Fetch the expense details from the database using the ID
            cursor.execute("SELECT * FROM expenses WHERE id = %s", (id,))
            expense = cursor.fetchone()
            cursor.close()
            conn.close()
            if expense:
                return render_template('edit_expense.html', expense=expense)
            else:
                return "Expense not found", 404
        
        elif request.method == 'POST':
            # Get the updated data from the form
            title = request.form['title']
            amount = request.form['amount']
            date = request.form['date']
            category = request.form['category']
            description = request.form.get('description', None)

            # Update the expense in the database
            cursor.execute("""
                UPDATE expenses
                SET title = %s, amount = %s, date = %s, category = %s, description = %s
                WHERE id = %s
            """, (title, amount, date, category, description, id))
            conn.commit()
            cursor.close()
            conn.close()

            return redirect(url_for('all_expenses'))
    
    except mysql.connector.Error as e:
        print(f"Error editing expense: {e}")
        return "Error editing expense in the database.", 500

@app.route('/monthly')
def monthly_summary():
    try:
        with get_db_connection() as conn:
            with conn.cursor(dictionary=True) as cursor:
                # Aggregate expenses by month and year
                cursor.execute("""
                    SELECT 
                        YEAR(date) AS year,
                        MONTH(date) AS month,
                        SUM(amount) AS total_amount
                    FROM expenses
                    GROUP BY YEAR(date), MONTH(date)
                    ORDER BY year DESC, month DESC
                """)
                summary = cursor.fetchall()
        return render_template('monthly.html', summary=summary)
    except mysql.connector.Error as e:
        print(f"Error fetching monthly summary: {e}")
        return "Error fetching data from the database.", 500


if __name__ == '__main__':
    app.run(debug=True)
