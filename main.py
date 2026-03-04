from fastmcp import FastMCP
import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

mcp = FastMCP(name="ExpenseTracker")

def init_db():
    with sqlite3.connect(DB_PATH) as c:
        c.execute("""
            CREATE TABLE IF NOT EXISTS expenses(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                subcategory TEXT DEFAULT '',
                note TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS salary(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                salary_amount REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS category_budget(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                budget_amount REAL NOT NULL
            )
        """)

init_db()

@mcp.tool()
def add_expense(date, amount, category, subcategory="", note=""):
    '''Add an expense entry to the database.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES(?, ?, ?, ?, ?)",
            (date, amount, category, subcategory, note)
        )
    return {"status": "ok", "id": cur.lastrowid}

@mcp.tool()
def list_expenses(start_date, end_date):
    '''List expense entries within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(
            """
            SELECT id, date, amount, category, subcategory, note        
            FROM expenses
            WHERE date BETWEEN ? AND ?
            ORDER BY id ASC
            """,
            (start_date, end_date)
        )
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]    

@mcp.tool()
def summarize(start_date, end_date, category=None):
    '''Summarize expenses by category within an inclusive date range.'''
    with sqlite3.connect(DB_PATH) as c:
        query = (
            """
            SELECT category, SUM(amount) AS total_amount
            FROM expenses
            WHERE date BETWEEN ? AND ?
            """
        )
        params = [start_date, end_date]

        if category:
            query += " AND category = ?"
            params.append(category)

        query += " GROUP BY category ORDER BY category ASC"

        cur = c.execute(query, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]

@mcp.tool()
def update_expense(expense_id: int, date: str = None, amount: float = None, category: str = None, subcategory: str = None, note: str = None) -> dict:
    '''Update an existing expense entry.'''
    updates = []
    params = []
    
    if date is not None:
        updates.append("date = ?")
        params.append(date)
    if amount is not None:
        updates.append("amount = ?")
        params.append(amount)
    if category is not None:
        updates.append("category = ?")
        params.append(category)
    if subcategory is not None:
        updates.append("subcategory = ?")
        params.append(subcategory)
    if note is not None:
        updates.append("note = ?")
        params.append(note)
        
    if not updates:
        return {"status": "error", "message": "No fields to update provided"}
        
    query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = ?"
    params.append(expense_id)
    
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute(query, tuple(params))
        if cur.rowcount == 0:
            return {"status": "error", "message": f"Expense {expense_id} not found"}
            
    return {"status": "ok", "message": f"Expense {expense_id} updated"}

@mcp.tool()
def delete_expense(expense_id: int) -> dict:
    '''Delete an expense entry by its ID.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        if cur.rowcount == 0:
            return {"status": "error", "message": f"Expense {expense_id} not found"}
    return {"status": "ok", "message": f"Expense {expense_id} deleted"}

@mcp.resource("expense://categories", mime_type="application/json")
def get_categories():
    # Read fresh each time so you can edit the file without restarting 
    with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
        return f.read()

@mcp.tool()
def set_salary(month: int, year: int, amount: float) -> dict:
    '''Allow the user to set or update their salary for a specific month and year.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id FROM salary WHERE month = ? AND year = ?", (month, year))
        row = cur.fetchone()
        if row:
            c.execute("UPDATE salary SET salary_amount = ? WHERE id = ?", (amount, row[0]))
        else:
            c.execute("INSERT INTO salary(month, year, salary_amount) VALUES(?, ?, ?)", (month, year, amount))
    return {"status": "ok", "month": month, "year": year, "salary": amount}

@mcp.tool()
def set_category_budget(category: str, month: int, year: int, amount: float) -> dict:
    '''Allow user to define a monthly budget for each category.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT id FROM category_budget WHERE category = ? AND month = ? AND year = ?", (category, month, year))
        row = cur.fetchone()
        if row:
            c.execute("UPDATE category_budget SET budget_amount = ? WHERE id = ?", (amount, row[0]))
        else:
            c.execute("INSERT INTO category_budget(category, month, year, budget_amount) VALUES(?, ?, ?, ?)", (category, month, year, amount))
    return {"status": "ok", "category": category, "month": month, "year": year, "budget": amount}

@mcp.tool()
def get_category_spending(month: int, year: int) -> list:
    '''Calculate total spending in each category for a specific month.'''
    with sqlite3.connect(DB_PATH) as c:
        date_pattern = f"{year}-{month:02d}-%"
        cur = c.execute("""
            SELECT category, SUM(amount) as spent
            FROM expenses
            WHERE date LIKE ?
            GROUP BY category
        """, (date_pattern,))
        return [{"category": r[0], "spent": r[1]} for r in cur.fetchall()]

@mcp.tool()
def get_category_budget_status(month: int, year: int) -> list:
    '''Combine budget and spending to show category budget status.'''
    with sqlite3.connect(DB_PATH) as c:
        date_pattern = f"{year}-{month:02d}-%"
        
        cur = c.execute("SELECT category, budget_amount FROM category_budget WHERE month = ? AND year = ?", (month, year))
        budgets = {r[0]: r[1] for r in cur.fetchall()}
        
        cur = c.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category", (date_pattern,))
        spending = {r[0]: r[1] for r in cur.fetchall()}
        
        all_categories = set(budgets.keys()).union(set(spending.keys()))
        
        result = []
        for cat in all_categories:
            b = budgets.get(cat, 0.0)
            s = spending.get(cat, 0.0)
            result.append({
                "category": cat,
                "budget": b,
                "spent": s,
                "remaining": b - s
            })
            
        return result

@mcp.tool()
def get_remaining_balance(month: int, year: int) -> dict:
    '''Calculate salary minus total expenses for that month.'''
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT salary_amount FROM salary WHERE month = ? AND year = ?", (month, year))
        row = cur.fetchone()
        salary = row[0] if row else 0.0
        
        date_pattern = f"{year}-{month:02d}-%"
        cur = c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (date_pattern,))
        row = cur.fetchone()
        expenses = row[0] if row and row[0] is not None else 0.0
        
        return {
            "salary": salary,
            "expenses": expenses,
            "remaining": salary - expenses
        }

@mcp.tool()
def get_total_available_balance(month: int, year: int) -> dict:
    '''Calculate total available balance by carrying forward remaining balance from the previous month.'''
    prev_month = month - 1
    prev_year = year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
        
    with sqlite3.connect(DB_PATH) as c:
        cur = c.execute("SELECT salary_amount FROM salary WHERE month = ? AND year = ?", (month, year))
        row = cur.fetchone()
        current_salary = row[0] if row else 0.0
        
        cur = c.execute("SELECT salary_amount FROM salary WHERE month = ? AND year = ?", (prev_month, prev_year))
        row = cur.fetchone()
        prev_salary = row[0] if row else 0.0
        
        prev_date_pattern = f"{prev_year}-{prev_month:02d}-%"
        cur = c.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (prev_date_pattern,))
        row = cur.fetchone()
        prev_spent = row[0] if row and row[0] is not None else 0.0
        
        prev_remaining = prev_salary - prev_spent
        
    return {
        "month": month,
        "year": year,
        "salary": current_salary,
        "previous_remaining": prev_remaining,
        "available_balance": current_salary + prev_remaining
    }

if __name__ == "__main__":
    # mcp.run(transport="http", host="0.0.0.0", port=8000)
    mcp.run()


