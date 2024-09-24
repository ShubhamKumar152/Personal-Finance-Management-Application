import sqlite3
import hashlib

# Database Connection and Setup
def get_db_connection():
    conn = sqlite3.connect('finance.db')
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )
    ''')

    # Create transactions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            category TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Create budget table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            limit_amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    conn.commit()
    conn.close()

# User Registration and Authentication
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    hashed_password = hashlib.sha256(password.encode()).hexdigest()

    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        conn.close()
        return "User registered successfully!"
    except sqlite3.IntegrityError:
        conn.close()
        return "Username already exists!"

def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()

    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = cursor.fetchone()

    conn.close()
    if user:
        return user[0]  # Return user_id
    else:
        return None

# Income and Expense Tracking
def add_transaction(user_id, type, amount, category, date):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO transactions (user_id, type, amount, category, date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, type, amount, category, date))
    conn.commit()
    conn.close()
    return True

def update_transaction(transaction_id, amount, category):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE transactions
        SET amount = ?, category = ?
        WHERE id = ?
    ''', (amount, category, transaction_id))
    conn.commit()
    conn.close()
    return True

def delete_transaction(transaction_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))
    conn.commit()
    conn.close()
    return True

# Financial Reports
def generate_monthly_report(user_id, month, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type, SUM(amount) FROM transactions 
        WHERE user_id = ? AND strftime('%m', date) = ? AND strftime('%Y', date) = ?
        GROUP BY type
    ''', (user_id, month, year))
    report = cursor.fetchall()
    conn.close()
    return report

def generate_yearly_report(user_id, year):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT type, SUM(amount) FROM transactions 
        WHERE user_id = ? AND strftime('%Y', date) = ?
        GROUP BY type
    ''', (user_id, year))
    report = cursor.fetchall()
    conn.close()
    return report

# Budgeting
def set_budget(user_id, category, limit_amount):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO budgets (user_id, category, limit_amount)
        VALUES (?, ?, ?)
    ''', (user_id, category, limit_amount))
    conn.commit()
    conn.close()
    return True

def check_budget(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT category, limit_amount, (SELECT SUM(amount) FROM transactions WHERE user_id = ? AND category = budgets.category)
        FROM budgets WHERE user_id = ?
    ''', (user_id, user_id))
    budgets = cursor.fetchall()
    conn.close()

    result = []
    for category, limit, spent in budgets:
        if spent is None:
            spent = 0
        if spent > limit:
            result.append(f"Alert: You have exceeded your budget for {category}!")
        else:
            result.append(f"You are within the budget for {category}.")
    return result

# Data Persistence: Backup and Restore
def backup_data():
    conn = get_db_connection()
    with open('backup.sql', 'w') as f:
        for line in conn.iterdump():
            f.write('%s\n' % line)
    conn.close()
    return "Data backup completed!"

def restore_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    with open('backup.sql', 'r') as f:
        sql_script = f.read()
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    return "Data restored successfully!"

# Main Application
def main():
    create_tables()

    print("Welcome to Personal Finance Management App!")
    while True:
        print("\nMenu:\n1. Register\n2. Login\n3. Exit")
        choice = input("Enter your choice: ")

        if choice == '1':
            username = input("Enter username: ")
            password = input("Enter password: ")
            message = register_user(username, password)
            print(message)
        
        elif choice == '2':
            username = input("Enter username: ")
            password = input("Enter password: ")
            user_id = login_user(username, password)
            
            if user_id:
                print("Login successful!")
                while True:
                    print("\nDashboard:\n1. Add Transaction\n2. Update Transaction\n3. Delete Transaction\n4. Generate Reports\n5. Set Budget\n6. Check Budget\n7. Backup Data\n8. Restore Data\n9. Logout")
                    choice = input("Enter your choice: ")

                    if choice == '1':
                        type = input("Enter type (Income/Expense): ")
                        amount = float(input("Enter amount: "))
                        category = input("Enter category (e.g., Food, Rent): ")
                        date = input("Enter date (YYYY-MM-DD): ")
                        result = add_transaction(user_id, type, amount, category, date)
                        print("Transaction added successfully!" if result else "Failed to add transaction.")

                    elif choice == '2':
                        transaction_id = int(input("Enter transaction ID to update: "))
                        amount = float(input("Enter new amount: "))
                        category = input("Enter new category: ")
                        result = update_transaction(transaction_id, amount, category)
                        print("Transaction updated successfully!" if result else "Failed to update transaction.")

                    elif choice == '3':
                        transaction_id = int(input("Enter transaction ID to delete: "))
                        result = delete_transaction(transaction_id)
                        print("Transaction deleted successfully!" if result else "Failed to delete transaction.")

                    elif choice == '4':
                        print("1. Monthly Report\n2. Yearly Report")
                        report_choice = input("Enter your choice: ")
                        if report_choice == '1':
                            month = input("Enter month (MM): ")
                            year = input("Enter year (YYYY): ")
                            report = generate_monthly_report(user_id, month, year)
                            print("Monthly Report:", report)
                        elif report_choice == '2':
                            year = input("Enter year (YYYY): ")
                            report = generate_yearly_report(user_id, year)
                            print("Yearly Report:", report)

                    elif choice == '5':
                        category = input("Enter category: ")
                        limit_amount = float(input("Enter limit amount: "))
                        result = set_budget(user_id, category, limit_amount)
                        print("Budget set successfully!" if result else "Failed to set budget.")

                    elif choice == '6':
                        result = check_budget(user_id)
                        for message in result:
                            print(message)

                    elif choice == '7':
                        message = backup_data()
                        print(message)

                    elif choice == '8':
                        message = restore_data()
                        print(message)

                    elif choice == '9':
                        print("Logged out successfully!")
                        break

        elif choice == '3':
            print("Thank you for using the Personal Finance Management App!")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
