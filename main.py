import os
import aiosqlite
import asyncio
import tempfile
from fastmcp import FastMCP

# Use temporary directory for better write access compatibility
TEMP_DIR = tempfile.gettempdir()
DB_PATH = os.path.join(TEMP_DIR, "expenses.db")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print(f"Database path: {DB_PATH}")

mcp = FastMCP("ExpenseTracker")

def init_db():
    """Initializes the database synchronously at module load."""
    try:
        import sqlite3
        with sqlite3.connect(DB_PATH) as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date TEXT NOT NULL,
                    amount REAL NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT ''
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS salary(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    salary_amount REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS category_budget(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    budget_amount REAL NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS savings_goal(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal_name TEXT,
                    target_amount REAL,
                    target_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

# Initialize database
init_db()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''Add a new expense entry to the database.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (?,?,?,?,?)",
                (date, amount, category, subcategory, note)
            )
            expense_id = cur.lastrowid
            await db.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE date BETWEEN ? AND ?
                ORDER BY date DESC, id DESC
                """,
                (start_date, end_date)
            )
            cols = [d[0] for d in cur.description]
            rows = await cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

@mcp.tool()
async def summarize(start_date: str, end_date: str, category: str = None):
    '''Summarize expenses by category within an inclusive date range.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses
                WHERE date BETWEEN ? AND ?
            """
            params = [start_date, end_date]
            if category:
                query += " AND category = ?"
                params.append(category)
            query += " GROUP BY category ORDER BY total_amount DESC"
            
            cur = await db.execute(query, params)
            cols = [d[0] for d in cur.description]
            rows = await cur.fetchall()
            return [dict(zip(cols, r)) for r in rows]
    except Exception as e:
        return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}

@mcp.tool()
async def update_expense(expense_id: int, date: str = None, amount: float = None, category: str = None, subcategory: str = None, note: str = None) -> dict:
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
    
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute(query, params)
            await db.commit()
            if cur.rowcount == 0:
                return {"status": "error", "message": f"Expense {expense_id} not found"}
            return {"status": "ok", "message": f"Expense {expense_id} updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    '''Delete an expense entry by its ID.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
            await db.commit()
            if cur.rowcount == 0:
                return {"status": "error", "message": f"Expense {expense_id} not found"}
            return {"status": "ok", "message": f"Expense {expense_id} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_salary(month: int, year: int, amount: float) -> dict:
    '''Set or update salary for a specific month and year.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT id FROM salary WHERE month = ? AND year = ?", (month, year))
            row = await cur.fetchone()
            if row:
                await db.execute("UPDATE salary SET salary_amount = ? WHERE id = ?", (amount, row[0]))
            else:
                await db.execute("INSERT INTO salary(month, year, salary_amount) VALUES(?, ?, ?)", (month, year, amount))
            await db.commit()
            return {"status": "ok", "month": month, "year": year, "salary": amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_category_budget(category: str, month: int, year: int, amount: float) -> dict:
    '''Define a monthly budget for each category.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT id FROM category_budget WHERE category = ? AND month = ? AND year = ?", (category, month, year))
            row = await cur.fetchone()
            if row:
                await db.execute("UPDATE category_budget SET budget_amount = ? WHERE id = ?", (amount, row[0]))
            else:
                await db.execute("INSERT INTO category_budget(category, month, year, budget_amount) VALUES(?, ?, ?, ?)", (category, month, year, amount))
            await db.commit()
            return {"status": "ok", "category": category, "month": month, "year": year, "budget": amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_category_budget_status(month: int, year: int) -> list:
    '''Combine budget and spending to show category budget status.'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE month = ? AND year = ?", (month, year))
            budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
            cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category", (date_pattern,))
            spending = {r[0]: r[1] for r in await cur.fetchall()}
        
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
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def get_remaining_balance(month: int, year: int) -> dict:
    '''Calculate salary minus total expenses for that month.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE month = ? AND year = ?", (month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0
            
            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (date_pattern,))
            row = await cur.fetchone()
            expenses = row[0] if row and row[0] is not None else 0.0
            
        return {
            "salary": salary,
            "expenses": expenses,
            "remaining": salary - expenses
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_weekly_expense_summary(year: int) -> list:
    '''Return total expenses grouped by week number.'''
    try:
        year_str = str(year)
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("""
                SELECT cast(strftime('%W', date) as integer) as week, SUM(amount) as total_expense
                FROM expenses
                WHERE strftime('%Y', date) = ?
                GROUP BY week
                ORDER BY week ASC
            """, (year_str,))
            rows = await cur.fetchall()
            return [{"week": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def get_ai_financial_advice(month: int, year: int) -> dict:
    '''Analyze financial data and generate AI-based advice.'''
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE month = ? AND year = ?", (month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0

            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE ?", (date_pattern,))
            row = await cur.fetchone()
            expenses = row[0] if row and row[0] is not None else 0.0

            cur = await db.execute("""
                SELECT category, SUM(amount) as total_spent
                FROM expenses
                WHERE date LIKE ?
                GROUP BY category
                ORDER BY total_spent DESC
                LIMIT 1
            """, (date_pattern,))
            row = await cur.fetchone()
            top_category = row[0] if row else None
            top_category_spent = row[1] if row else 0.0

        remaining = salary - expenses
        advice = []
        if salary > 0:
            if expenses > 0.8 * salary:
                advice.append("Your spending is quite high compared to your income.")
            savings_pct = (remaining / salary) * 100
            if savings_pct < 10:
                advice.append("Try increasing your savings to at least 20% of your salary.")
            elif savings_pct >= 20:
                advice.append(f"You are saving {savings_pct:.0f}% of your income, which is a good financial habit.")
        
        if top_category:
            advice.append(f"Your highest spending category is {top_category}.")

        return {
            "salary": salary,
            "expenses": expenses,
            "remaining": remaining,
            "top_spending_category": top_category if top_category else "None",
            "advice": advice
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.resource("expense:///categories", mime_type="application/json")
def categories():
    '''Provide expense categories.'''
    try:
        default_categories = {
            "categories": ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Bills & Utilities", "Healthcare", "Travel", "Education", "Business", "Other"]
        }
        try:
            with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            import json
            return json.dumps(default_categories, indent=2)
    except Exception as e:
        return f'{{"error": "Could not load categories: {str(e)}"}}'

if __name__ == "__main__":
    mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
