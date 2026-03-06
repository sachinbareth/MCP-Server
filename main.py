# import os
# import psycopg
# from psycopg.rows import tuple_row
# import asyncio
# import sys
# if sys.platform == 'win32':
#     asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
# import tempfile
# from fastmcp import FastMCP

# # Use temporary directory for better write access compatibility
# TEMP_DIR = tempfile.gettempdir()
# from dotenv import load_dotenv
# load_dotenv()
# DB_URL = os.environ.get("DB_URL")
# if not DB_URL:
#     raise ValueError("DB_URL environment variable is must be set in .env")
# CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

# print("Using PostgreSQL Database")

# mcp = FastMCP("ExpenseTracker")

# def init_db():
#     """Initializes the database synchronously at module load."""
#     try:
#         import psycopg
#         with psycopg.connect(DB_URL) as db:
            
#             db.execute("""
#                 CREATE TABLE IF NOT EXISTS expenses(
#                     id SERIAL PRIMARY KEY,
#                     date TEXT NOT NULL,
#                     amount NUMERIC NOT NULL,
#                     category TEXT NOT NULL,
#                     subcategory TEXT DEFAULT '',
#                     note TEXT DEFAULT ''
#                 )
#             """)
#             db.execute("""
#                 CREATE TABLE IF NOT EXISTS salary(
#                     id SERIAL PRIMARY KEY,
#                     month INTEGER NOT NULL,
#                     year INTEGER NOT NULL,
#                     salary_amount NUMERIC NOT NULL
#                 )
#             """)
#             db.execute("""
#                 CREATE TABLE IF NOT EXISTS category_budget(
#                     id SERIAL PRIMARY KEY,
#                     category TEXT NOT NULL,
#                     month INTEGER NOT NULL,
#                     year INTEGER NOT NULL,
#                     budget_amount NUMERIC NOT NULL
#                 )
#             """)
#             db.execute("""
#                 CREATE TABLE IF NOT EXISTS savings_goal(
#                     id SERIAL PRIMARY KEY,
#                     goal_name TEXT,
#                     target_amount NUMERIC,
#                     target_date TEXT,
#                     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
#                 )
#             """)
#             db.commit()
#             print("Database initialized successfully with write access")
#     except Exception as e:
#         print(f"Database initialization error: {e}")
#         raise

# # Initialize database
# init_db()

# @mcp.tool()
# async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
#     '''Add a new expense entry to the database.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute(
#                 "INSERT INTO expenses(date, amount, category, subcategory, note) VALUES (%s,%s,%s,%s,%s) RETURNING id",
#                 (date, amount, category, subcategory, note)
#             )
#             row = await cur.fetchone()
#             expense_id = row[0] if row else None
#             await db.commit()
#             return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
#     except Exception as e:
#         return {"status": "error", "message": f"Database error: {str(e)}"}

# @mcp.tool()
# async def list_expenses(start_date: str, end_date: str):
#     '''List expense entries within an inclusive date range.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute(
#                 """
#                 SELECT id, date, amount, category, subcategory, note
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 ORDER BY date DESC, id DESC
#                 """,
#                 (start_date, end_date)
#             )
#             cols = [d[0] for d in cur.description]
#             rows = await cur.fetchall()
#             return [dict(zip(cols, r)) for r in rows]
#     except Exception as e:
#         return {"status": "error", "message": f"Error listing expenses: {str(e)}"}

# @mcp.tool()
# async def summarize(start_date: str, end_date: str, category: str = None):
#     '''Summarize expenses by category within an inclusive date range.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             query = """
#                 SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#             """
#             params = [start_date, end_date]
#             if category:
#                 query += " AND category = %s"
#                 params.append(category)
#             query += " GROUP BY category ORDER BY total_amount DESC"
            
#             cur = await db.execute(query, params)
#             cols = [d[0] for d in cur.description]
#             rows = await cur.fetchall()
#             return [dict(zip(cols, r)) for r in rows]
#     except Exception as e:
#         return {"status": "error", "message": f"Error summarizing expenses: {str(e)}"}

# @mcp.tool()
# async def update_expense(expense_id: int, date: str = None, amount: float = None, category: str = None, subcategory: str = None, note: str = None) -> dict:
#     '''Update an existing expense entry.'''
#     updates = []
#     params = []
#     if date is not None:
#         updates.append("date = %s")
#         params.append(date)
#     if amount is not None:
#         updates.append("amount = %s")
#         params.append(amount)
#     if category is not None:
#         updates.append("category = %s")
#         params.append(category)
#     if subcategory is not None:
#         updates.append("subcategory = %s")
#         params.append(subcategory)
#     if note is not None:
#         updates.append("note = %s")
#         params.append(note)
#     if not updates:
#         return {"status": "error", "message": "No fields to update provided"}
        
#     query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = %s"
#     params.append(expense_id)
    
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute(query, params)
#             await db.commit()
#             if cur.rowcount == 0:
#                 return {"status": "error", "message": f"Expense {expense_id} not found"}
#             return {"status": "ok", "message": f"Expense {expense_id} updated"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def delete_expense(expense_id: int) -> dict:
#     '''Delete an expense entry by its ID.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("DELETE FROM expenses WHERE id = %s", (expense_id,))
#             await db.commit()
#             if cur.rowcount == 0:
#                 return {"status": "error", "message": f"Expense {expense_id} not found"}
#             return {"status": "ok", "message": f"Expense {expense_id} deleted"}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def set_salary(month: int, year: int, amount: float) -> dict:
#     '''Set or update salary for a specific month and year.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT id FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             if row:
#                 await db.execute("UPDATE salary SET salary_amount = %s WHERE id = %s", (amount, row[0]))
#             else:
#                 await db.execute("INSERT INTO salary(month, year, salary_amount) VALUES(%s, %s, %s)", (month, year, amount))
#             await db.commit()
#             return {"status": "ok", "month": month, "year": year, "salary": amount}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def set_category_budget(category: str, month: int, year: int, amount: float) -> dict:
#     '''Define a monthly budget for each category.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT id FROM category_budget WHERE category = %s AND month = %s AND year = %s", (category, month, year))
#             row = await cur.fetchone()
#             if row:
#                 await db.execute("UPDATE category_budget SET budget_amount = %s WHERE id = %s", (amount, row[0]))
#             else:
#                 await db.execute("INSERT INTO category_budget(category, month, year, budget_amount) VALUES(%s, %s, %s, %s)", (category, month, year, amount))
#             await db.commit()
#             return {"status": "ok", "category": category, "month": month, "year": year, "budget": amount}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_category_budget_status(month: int, year: int) -> list:
#     '''Combine budget and spending to show category budget status.'''
#     try:
#         date_pattern = f"{year}-{month:02d}-%"
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE month = %s AND year = %s", (month, year))
#             budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
#             cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE %s GROUP BY category", (date_pattern,))
#             spending = {r[0]: r[1] for r in await cur.fetchall()}
        
#         all_categories = set(budgets.keys()).union(set(spending.keys()))
#         result = []
#         for cat in all_categories:
#             b = budgets.get(cat, 0.0)
#             s = spending.get(cat, 0.0)
#             result.append({
#                 "category": cat,
#                 "budget": b,
#                 "spent": s,
#                 "remaining": b - s
#             })
#         return result
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_remaining_balance(month: int, year: int) -> dict:
#     '''Calculate salary minus total expenses for that month.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             salary = row[0] if row else 0.0
            
#             date_pattern = f"{year}-{month:02d}-%"
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern,))
#             row = await cur.fetchone()
#             expenses = row[0] if row and row[0] is not None else 0.0
            
#         return {
#             "salary": salary,
#             "expenses": expenses,
#             "remaining": salary - expenses
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_weekly_expense_summary(year: int) -> list:
#     '''Return total expenses grouped by week number.'''
#     try:
#         year_str = str(year)
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT cast(extract(week from date::date) as integer) as week, SUM(amount) as total_expense
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY week
#                 ORDER BY week ASC
#             """, (year_str,))
#             rows = await cur.fetchall()
#             return [{"week": r[0], "total_expense": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_ai_financial_advice(month: int, year: int) -> dict:
#     '''Analyze financial data and generate AI-based advice.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             salary = row[0] if row else 0.0

#             date_pattern = f"{year}-{month:02d}-%"
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern,))
#             row = await cur.fetchone()
#             expenses = row[0] if row and row[0] is not None else 0.0

#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as total_spent
#                 FROM expenses
#                 WHERE date LIKE %s
#                 GROUP BY category
#                 ORDER BY total_spent DESC
#                 LIMIT 1
#             """, (date_pattern,))
#             row = await cur.fetchone()
#             top_category = row[0] if row else None
#             top_category_spent = row[1] if row else 0.0

#         remaining = salary - expenses
#         advice = []
#         if salary > 0:
#             if expenses > 0.8 * salary:
#                 advice.append("Your spending is quite high compared to your income.")
#             savings_pct = (remaining / salary) * 100
#             if savings_pct < 10:
#                 advice.append("Try increasing your savings to at least 20% of your salary.")
#             elif savings_pct >= 20:
#                 advice.append(f"You are saving {savings_pct:.0f}% of your income, which is a good financial habit.")
        
#         if top_category:
#             advice.append(f"Your highest spending category is {top_category}.")

#         return {
#             "salary": salary,
#             "expenses": expenses,
#             "remaining": remaining,
#             "top_spending_category": top_category if top_category else "None",
#             "advice": advice
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_category_spending(month: int, year: int) -> list:
#     '''Calculate total spending in each category for a specific month.'''
#     try:
#         date_pattern = f"{year}-{month:02d}-%"
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as spent
#                 FROM expenses
#                 WHERE date LIKE %s
#                 GROUP BY category
#             """, (date_pattern,))
#             rows = await cur.fetchall()
#             return [{"category": r[0], "spent": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_total_available_balance(month: int, year: int) -> dict:
#     '''Calculate total available balance by carrying forward remaining balance from the previous month.'''
#     try:
#         prev_month = month - 1
#         prev_year = year
#         if prev_month == 0:
#             prev_month = 12
#             prev_year -= 1
            
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             # Current salary
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             current_salary = row[0] if row else 0.0
            
#             # Previous salary
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (prev_month, prev_year))
#             row = await cur.fetchone()
#             prev_salary = row[0] if row else 0.0
            
#             # Previous expenses
#             prev_date_pattern = f"{prev_year}-{prev_month:02d}-%"
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (prev_date_pattern,))
#             row = await cur.fetchone()
#             prev_spent = row[0] if row and row[0] is not None else 0.0
            
#             prev_remaining = prev_salary - prev_spent
            
#         return {
#             "month": month,
#             "year": year,
#             "salary": current_salary,
#             "previous_remaining": prev_remaining,
#             "available_balance": current_salary + prev_remaining
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_daily_expense_summary(start_date: str, end_date: str) -> list:
#     '''Return total expenses grouped by date.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT date, SUM(amount) as total_expense
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 GROUP BY date
#                 ORDER BY date ASC
#             """, (start_date, end_date))
#             rows = await cur.fetchall()
#             return [{"date": r[0], "total_expense": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_monthly_expense_summary(year: int) -> list:
#     '''Return expenses grouped by month.'''
#     try:
#         year_str = str(year)
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT substring(date from 6 for 2) as month, SUM(amount) as total_expense
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY month
#                 ORDER BY month ASC
#             """, (year_str,))
#             rows = await cur.fetchall()
#             return [{"month": r[0], "total_expense": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_yearly_expense_summary() -> list:
#     '''Return total expenses grouped by year.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT substring(date from 1 for 4) as year, SUM(amount) as total_expense
#                 FROM expenses
#                 GROUP BY year
#                 ORDER BY year ASC
#             """)
#             rows = await cur.fetchall()
#             return [{"year": r[0], "total_expense": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_category_spending_report(start_date: str, end_date: str) -> list:
#     '''Return total spending per category.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as total_spent
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 GROUP BY category
#                 ORDER BY category ASC
#             """, (start_date, end_date))
#             rows = await cur.fetchall()
#             return [{"category": r[0], "total_spent": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_top_spending_categories(start_date: str, end_date: str, limit: int = 5) -> list:
#     '''Return categories with highest spending.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as total_spent
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 GROUP BY category
#                 ORDER BY total_spent DESC
#                 LIMIT %s
#             """, (start_date, end_date, limit))
#             rows = await cur.fetchall()
#             return [{"category": r[0], "total_spent": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def compare_monthly_expenses(month1: int, year1: int, month2: int, year2: int) -> dict:
#     '''Return comparison between two months.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             date_pattern1 = f"{year1}-{month1:02d}-%"
#             date_pattern2 = f"{year2}-{month2:02d}-%"
            
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern1,))
#             row = await cur.fetchone()
#             m1_total = row[0] if row and row[0] is not None else 0.0
            
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern2,))
#             row = await cur.fetchone()
#             m2_total = row[0] if row and row[0] is not None else 0.0
            
#             return {
#                 "month1_total": m1_total,
#                 "month2_total": m2_total,
#                 "difference": abs(m1_total - m2_total)
#             }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_expense_trend(year: int) -> list:
#     '''Return monthly spending trend data.'''
#     try:
#         year_str = str(year)
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT substring(date from 6 for 2) as month, SUM(amount) as total_expense
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY month
#                 ORDER BY month ASC
#             """, (year_str,))
#             rows = await cur.fetchall()
#             return [{"month": r[0], "total_expense": r[1]} for r in rows]
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def check_budget_exceeded(month: int, year: int) -> list:
#     '''Check if actual spending exceeds the defined budget for any category.'''
#     try:
#         date_pattern = f"{year}-{month:02d}-%"
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE month = %s AND year = %s", (month, year))
#             budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
#             cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE %s GROUP BY category", (date_pattern,))
#             spending = {r[0]: r[1] for r in await cur.fetchall()}
            
#         alerts = []
#         for cat, budget in budgets.items():
#             spent = spending.get(cat, 0.0)
#             if spent > budget:
#                 alerts.append({
#                     "category": cat,
#                     "budget": budget,
#                     "spent": spent,
#                     "alert": "Budget exceeded"
#                 })
#         return alerts
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def check_budget_near_limit(month: int, year: int, threshold: float = 0.8) -> list:
#     '''Check if spending is near the budget limit (>= threshold * budget).'''
#     try:
#         date_pattern = f"{year}-{month:02d}-%"
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE month = %s AND year = %s", (month, year))
#             budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
#             cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE %s GROUP BY category", (date_pattern,))
#             spending = {r[0]: r[1] for r in await cur.fetchall()}
            
#         alerts = []
#         for cat, budget in budgets.items():
#             spent = spending.get(cat, 0.0)
#             if budget > 0 and spent >= (threshold * budget):
#                 alerts.append({
#                     "category": cat,
#                     "budget": budget,
#                     "spent": spent,
#                     "usage_percent": round((spent / budget) * 100, 2),
#                     "alert": "Budget almost reached"
#                 })
#         return alerts
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def detect_high_spending(start_date: str, end_date: str) -> list:
#     '''Identify categories where spending is unusually high (e.g. greater than average category spending).'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as total_spent
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 GROUP BY category
#             """, (start_date, end_date))
#             rows = await cur.fetchall()
            
#         categories_spending = [{"category": r[0], "spent": r[1]} for r in rows]
#         if not categories_spending:
#             return []
            
#         total_spending = sum(item["spent"] for item in categories_spending)
#         avg_spending = total_spending / len(categories_spending)
        
#         alerts = []
#         for item in categories_spending:
#             if item["spent"] > avg_spending:
#                 alerts.append({
#                     "category": item["category"],
#                     "spent": item["spent"],
#                     "avg_spending": round(avg_spending, 2),
#                     "alert": "High spending detected"
#                 })
#         return alerts
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def check_daily_spending_alert(date: str, limit: float) -> dict:
#     '''Check if total spending for a specific day exceeds the given limit.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date = %s", (date,))
#             row = await cur.fetchone()
#             spent = row[0] if row and row[0] is not None else 0.0
            
#         if spent > limit:
#             return {
#                 "date": date,
#                 "spent": spent,
#                 "limit": limit,
#                 "alert": "Daily spending limit exceeded"
#             }
#         return {}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def check_monthly_overspending(month: int, year: int) -> dict:
#     '''Check if total expenses for the month exceed the salary for that month.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             if not row:
#                 return {}
#             salary = row[0]
            
#             date_pattern = f"{year}-{month:02d}-%"
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern,))
#             row = await cur.fetchone()
#             spent = row[0] if row and row[0] is not None else 0.0
            
#         if spent > salary:
#             return {
#                 "salary": salary,
#                 "expenses": spent,
#                 "alert": "Monthly overspending detected"
#             }
#         return {}
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def set_savings_goal(goal_name: str, target_amount: float, target_date: str) -> dict:
#     '''Set a new savings goal.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             await db.execute(
#                 "INSERT INTO savings_goal(goal_name, target_amount, target_date) VALUES(%s, %s, %s)",
#                 (goal_name, target_amount, target_date)
#             )
#             await db.commit()
#         return {
#             "status": "ok",
#             "goal_name": goal_name,
#             "target_amount": target_amount,
#             "target_date": target_date
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_savings_progress(month: int, year: int) -> dict:
#     '''Calculate savings progress for a specific month (Salary - Expenses).'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             salary = row[0] if row else 0.0

#             date_pattern = f"{year}-{month:02d}-%"
#             cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE date LIKE %s", (date_pattern,))
#             row = await cur.fetchone()
#             expenses = row[0] if row and row[0] is not None else 0.0

#         return {
#             "month": month,
#             "year": year,
#             "salary": salary,
#             "expenses": expenses,
#             "saved": salary - expenses
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def get_monthly_savings(year: int) -> list:
#     '''Return savings for each month in a given year.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             # Get salary for each month
#             cur = await db.execute("SELECT month, salary_amount FROM salary WHERE year = %s", (year,))
#             salaries = {r[0]: r[1] for r in await cur.fetchall()}

#             # Get expenses for each month
#             year_str = str(year)
#             cur = await db.execute("""
#                 SELECT cast(substring(date from 6 for 2) as integer) as month, SUM(amount)
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY month
#             """, (year_str,))
#             expenses_dict = {r[0]: r[1] for r in await cur.fetchall()}

#         all_months = set(salaries.keys()).union(set(expenses_dict.keys()))
#         result = []
#         for m in sorted(all_months):
#             s = salaries.get(m, 0.0)
#             e = expenses_dict.get(m, 0.0)
#             result.append({
#                 "month": m,
#                 "saved": s - e
#             })
#         return result
#     except Exception as e:
#         return [{"status": "error", "message": str(e)}]

# @mcp.tool()
# async def get_total_saved_money() -> dict:
#     '''Calculate total savings across all months (Total Salary - Total Expenses).'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT SUM(salary_amount) FROM salary")
#             row = await cur.fetchone()
#             total_salary = row[0] if row and row[0] is not None else 0.0

#             cur = await db.execute("SELECT SUM(amount) FROM expenses")
#             row = await cur.fetchone()
#             total_expenses = row[0] if row and row[0] is not None else 0.0

#         return {
#             "total_saved": total_salary - total_expenses
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def suggest_savings_amount(month: int, year: int) -> dict:
#     '''Suggest a savings amount for a specific month (e.g., 20% of salary).'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT salary_amount FROM salary WHERE month = %s AND year = %s", (month, year))
#             row = await cur.fetchone()
#             salary = row[0] if row else 0.0

#         return {
#             "salary": salary,
#             "recommended_savings": salary * 0.20
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def generate_monthly_spending_chart(year: int) -> dict:
#     '''Generate a bar chart showing monthly expenses.'''
#     try:
#         year_str = str(year)
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT substring(date from 6 for 2) as month, SUM(amount) as amount
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY month
#                 ORDER BY month ASC
#             """, (year_str,))
#             rows = await cur.fetchall()
            
#         month_names = {
#             "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
#             "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
#         }
        
#         data = []
#         for r in rows:
#             data.append({"month": month_names.get(r[0], r[0]), "amount": r[1]})
            
#         return {
#             "chart_type": "bar",
#             "title": "Monthly Spending",
#             "data": data
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def generate_category_pie_chart(start_date: str, end_date: str) -> dict:
#     '''Generate a pie chart showing spending distribution.'''
#     try:
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT category, SUM(amount) as amount
#                 FROM expenses
#                 WHERE date BETWEEN %s AND %s
#                 GROUP BY category
#                 ORDER BY amount DESC
#             """, (start_date, end_date))
#             rows = await cur.fetchall()
            
#         categories = []
#         values = []
#         for r in rows:
#             categories.append(r[0])
#             values.append(r[1])
            
#         return {
#             "chart_type": "pie",
#             "categories": categories,
#             "values": values
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def generate_expense_trend_graph(year: int) -> dict:
#     '''Plot a line graph showing spending trend over time.'''
#     try:
#         year_str = str(year)
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("""
#                 SELECT substring(date from 6 for 2) as month, SUM(amount) as amount
#                 FROM expenses
#                 WHERE substring(date from 1 for 4) = %s
#                 GROUP BY month
#                 ORDER BY month ASC
#             """, (year_str,))
#             rows = await cur.fetchall()
            
#         month_names = {
#             "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
#             "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
#         }
        
#         data = []
#         for r in rows:
#             data.append({"month": month_names.get(r[0], r[0]), "amount": r[1]})
            
#         return {
#             "chart_type": "line",
#             "title": "Expense Trend",
#             "data": data
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}

# @mcp.tool()
# async def generate_budget_vs_spending_chart(month: int, year: int) -> dict:
#     '''Generate a bar chart comparing budget vs actual spending.'''
#     try:
#         date_pattern = f"{year}-{month:02d}-%"
#         async with await psycopg.AsyncConnection.connect(DB_URL) as db:
#             cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE month = %s AND year = %s", (month, year))
#             budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
#             cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE date LIKE %s GROUP BY category", (date_pattern,))
#             spending = {r[0]: r[1] for r in await cur.fetchall()}
            
#         categories = []
#         budget_values = []
#         spent_values = []
        
#         all_categories = sorted(list(set(budgets.keys()).union(set(spending.keys()))))
#         for cat in all_categories:
#             categories.append(cat)
#             budget_values.append(budgets.get(cat, 0.0))
#             spent_values.append(spending.get(cat, 0.0))
            
#         return {
#             "chart_type": "bar",
#             "categories": categories,
#             "budget": budget_values,
#             "spent": spent_values
#         }
#     except Exception as e:
#         return {"status": "error", "message": str(e)}





# @mcp.resource("expense:///categories", mime_type="application/json")
# def categories():
#     '''Provide expense categories.'''
#     try:
#         default_categories = {
#             "categories": ["Food & Dining", "Transportation", "Shopping", "Entertainment", "Bills & Utilities", "Healthcare", "Travel", "Education", "Business", "Other"]
#         }
#         try:
#             with open(CATEGORIES_PATH, "r", encoding="utf-8") as f:
#                 return f.read()
#         except FileNotFoundError:
#             import json
#             return json.dumps(default_categories, indent=2)
#     except Exception as e:
#         return f'{{"error": "Could not load categories: {str(e)}"}}'

# if __name__ == "__main__":
#     mcp.run(transport="http", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))



import os
import psycopg
from psycopg.rows import tuple_row
import asyncio
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
import tempfile
from fastmcp import FastMCP

# Use temporary directory for better write access compatibility
TEMP_DIR = tempfile.gettempdir()
from dotenv import load_dotenv
load_dotenv()
# ─── Database Configuration ────────────────────────────────────────────────────
# db_url_raw = os.environ.get("DATABASE_URL")
# if not db_url_raw:
#     raise ValueError("DATABASE_URL environment variable must be set in .env")

# # Clean the URL for psycopg (remove sqlalchemy +asyncpg/aiosqlite prefixes)
# DB_URL = db_url_raw.replace("postgresql+asyncpg://", "postgresql://")
# DB_URL = DB_URL.replace("sqlite+aiosqlite:///", "sqlite:///")

# CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")
# Use temporary directory for better write access compatibility
DB_URL = os.environ.get("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is must be set in .env")
CATEGORIES_PATH = os.path.join(os.path.dirname(__file__), "categories.json")

print("Using PostgreSQL Database")

mcp = FastMCP("ExpenseTracker")

# Note: We default user_id to 1 for all agent operations to match the main user.
DEFAULT_USER_ID = 1

def init_db():
    """Initializes the database synchronously at module load."""
    try:
        import psycopg
        with psycopg.connect(DB_URL) as db:
            # We ensure tables match the backend's SQLAlchemy schema
            db.execute("""
                CREATE TABLE IF NOT EXISTS expenses(
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    date TEXT NOT NULL,
                    amount NUMERIC NOT NULL,
                    category TEXT NOT NULL,
                    subcategory TEXT DEFAULT '',
                    note TEXT DEFAULT '',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS salary(
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    salary_amount NUMERIC NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS category_budget(
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    category TEXT NOT NULL,
                    month INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    budget_amount NUMERIC NOT NULL
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS savings_goal(
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    goal_name TEXT,
                    target_amount NUMERIC,
                    target_date TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.execute("""
                CREATE TABLE IF NOT EXISTS chat_history(
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL DEFAULT 1,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            db.commit()
            print("Database initialized successfully with write access")
    except Exception as e:
        print(f"Database initialization error: {e}")
        # We don't raise here to allow the server to potentially start if DB is already up
        pass

# Initialize database
init_db()

@mcp.tool()
async def add_expense(date: str, amount: float, category: str, subcategory: str = "", note: str = ""):
    '''Add a new expense entry to the database.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute(
                "INSERT INTO expenses(user_id, date, amount, category, subcategory, note, created_at) VALUES (%s,%s,%s,%s,%s,%s,now()) RETURNING id",
                (DEFAULT_USER_ID, date, amount, category, subcategory, note)
            )
            row = await cur.fetchone()
            expense_id = row[0] if row else None
            await db.commit()
            return {"status": "success", "id": expense_id, "message": "Expense added successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Database error: {str(e)}"}

@mcp.tool()
async def list_expenses(start_date: str, end_date: str):
    '''List expense entries within an inclusive date range.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute(
                """
                SELECT id, date, amount, category, subcategory, note
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                ORDER BY date DESC, id DESC
                """,
                (DEFAULT_USER_ID, start_date, end_date)
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
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            query = """
                SELECT category, SUM(amount) AS total_amount, COUNT(*) as count
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
            """
            params = [DEFAULT_USER_ID, start_date, end_date]
            if category:
                query += " AND category = %s"
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
        updates.append("date = %s")
        params.append(date)
    if amount is not None:
        updates.append("amount = %s")
        params.append(amount)
    if category is not None:
        updates.append("category = %s")
        params.append(category)
    if subcategory is not None:
        updates.append("subcategory = %s")
        params.append(subcategory)
    if note is not None:
        updates.append("note = %s")
        params.append(note)
    if not updates:
        return {"status": "error", "message": "No fields to update provided"}
        
    query = f"UPDATE expenses SET {', '.join(updates)} WHERE id = %s AND user_id = %s"
    params.extend([expense_id, DEFAULT_USER_ID])
    
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute(query, params)
            await db.commit()
            if cur.rowcount == 0:
                return {"status": "error", "message": f"Expense {expense_id} not found or unauthorized"}
            return {"status": "ok", "message": f"Expense {expense_id} updated"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def delete_expense(expense_id: int) -> dict:
    '''Delete an expense entry by its ID.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (expense_id, DEFAULT_USER_ID))
            await db.commit()
            if cur.rowcount == 0:
                return {"status": "error", "message": f"Expense {expense_id} not found or unauthorized"}
            return {"status": "ok", "message": f"Expense {expense_id} deleted"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_salary(month: int, year: int, amount: float) -> dict:
    '''Set or update salary for a specific month and year.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT id FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            if row:
                await db.execute("UPDATE salary SET salary_amount = %s WHERE id = %s", (amount, row[0]))
            else:
                await db.execute("INSERT INTO salary(user_id, month, year, salary_amount) VALUES(%s, %s, %s, %s)", (DEFAULT_USER_ID, month, year, amount))
            await db.commit()
            return {"status": "ok", "month": month, "year": year, "salary": amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_category_budget(category: str, month: int, year: int, amount: float) -> dict:
    '''Define a monthly budget for each category.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT id FROM category_budget WHERE user_id = %s AND category = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, category, month, year))
            row = await cur.fetchone()
            if row:
                await db.execute("UPDATE category_budget SET budget_amount = %s WHERE id = %s", (amount, row[0]))
            else:
                await db.execute("INSERT INTO category_budget(user_id, category, month, year, budget_amount) VALUES(%s, %s, %s, %s, %s)", (DEFAULT_USER_ID, category, month, year, amount))
            await db.commit()
            return {"status": "ok", "category": category, "month": month, "year": year, "budget": amount}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_category_budget_status(month: int, year: int) -> list:
    '''Combine budget and spending to show category budget status.'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
            cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s GROUP BY category", (DEFAULT_USER_ID, date_pattern,))
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
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0
            
            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern,))
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
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT cast(extract(week from date::date) as integer) as week, SUM(amount) as total_expense
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY week
                ORDER BY week ASC
            """, (DEFAULT_USER_ID, year_str,))
            rows = await cur.fetchall()
            return [{"week": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def get_ai_financial_advice(month: int, year: int) -> dict:
    '''Analyze financial data and generate AI-based advice.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0

            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern,))
            row = await cur.fetchone()
            expenses = row[0] if row and row[0] is not None else 0.0

            cur = await db.execute("""
                SELECT category, SUM(amount) as total_spent
                FROM expenses
                WHERE user_id = %s AND date LIKE %s
                GROUP BY category
                ORDER BY total_spent DESC
                LIMIT 1
            """, (DEFAULT_USER_ID, date_pattern,))
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

@mcp.tool()
async def get_category_spending(month: int, year: int) -> list:
    '''Calculate total spending in each category for a specific month.'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT category, SUM(amount) as spent
                FROM expenses
                WHERE user_id = %s AND date LIKE %s
                GROUP BY category
            """, (DEFAULT_USER_ID, date_pattern,))
            rows = await cur.fetchall()
            return [{"category": r[0], "spent": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_total_available_balance(month: int, year: int) -> dict:
    '''Calculate total available balance by carrying forward remaining balance from the previous month.'''
    try:
        prev_month = month - 1
        prev_year = year
        if prev_month == 0:
            prev_month = 12
            prev_year -= 1
            
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            # Current salary
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            current_salary = row[0] if row else 0.0
            
            # Previous salary
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, prev_month, prev_year))
            row = await cur.fetchone()
            prev_salary = row[0] if row else 0.0
            
            # Previous expenses
            prev_date_pattern = f"{prev_year}-{prev_month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, prev_date_pattern,))
            row = await cur.fetchone()
            prev_spent = row[0] if row and row[0] is not None else 0.0
            
            prev_remaining = prev_salary - prev_spent
            
        return {
            "month": month,
            "year": year,
            "salary": current_salary,
            "previous_remaining": prev_remaining,
            "available_balance": current_salary + prev_remaining
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_daily_expense_summary(start_date: str, end_date: str) -> list:
    '''Return total expenses grouped by date.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT date, SUM(amount) as total_expense
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                GROUP BY date
                ORDER BY date ASC
            """, (DEFAULT_USER_ID, start_date, end_date))
            rows = await cur.fetchall()
            return [{"date": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_monthly_expense_summary(year: int) -> list:
    '''Return expenses grouped by month.'''
    try:
        year_str = str(year)
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT substring(date from 6 for 2) as month, SUM(amount) as total_expense
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY month
                ORDER BY month ASC
            """, (DEFAULT_USER_ID, year_str,))
            rows = await cur.fetchall()
            return [{"month": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_yearly_expense_summary() -> list:
    '''Return total expenses grouped by year.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT substring(date from 1 for 4) as year, SUM(amount) as total_expense
                FROM expenses
                WHERE user_id = %s
                GROUP BY year
                ORDER BY year ASC
            """, (DEFAULT_USER_ID,))
            rows = await cur.fetchall()
            return [{"year": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_category_spending_report(start_date: str, end_date: str) -> list:
    '''Return total spending per category.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT category, SUM(amount) as total_spent
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                GROUP BY category
                ORDER BY category ASC
            """, (DEFAULT_USER_ID, start_date, end_date))
            rows = await cur.fetchall()
            return [{"category": r[0], "total_spent": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_top_spending_categories(start_date: str, end_date: str, limit: int = 5) -> list:
    '''Return categories with highest spending.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT category, SUM(amount) as total_spent
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                GROUP BY category
                ORDER BY total_spent DESC
                LIMIT %s
            """, (DEFAULT_USER_ID, start_date, end_date, limit))
            rows = await cur.fetchall()
            return [{"category": r[0], "total_spent": r[1]} for r in rows]
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def compare_monthly_expenses(month1: int, year1: int, month2: int, year2: int) -> dict:
    '''Return comparison between two months.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            date_pattern1 = f"{year1}-{month1:02d}-%"
            date_pattern2 = f"{year2}-{month2:02d}-%"
            
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern1,))
            row = await cur.fetchone()
            m1_total = row[0] if row and row[0] is not None else 0.0
            
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern2,))
            row = await cur.fetchone()
            m2_total = row[0] if row and row[0] is not None else 0.0
            
            return {
                "month1_total": m1_total,
                "month2_total": m2_total,
                "difference": abs(m1_total - m2_total)
            }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_expense_trend(year: int) -> list:
    '''Return monthly spending trend data.'''
    try:
        year_str = str(year)
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT substring(date from 6 for 2) as month, SUM(amount) as total_expense
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY month
                ORDER BY month ASC
            """, (DEFAULT_USER_ID, year_str,))
            rows = await cur.fetchall()
            return [{"month": r[0], "total_expense": r[1]} for r in rows]
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def check_budget_exceeded(month: int, year: int) -> list:
    '''Check if actual spending exceeds the defined budget for any category.'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
            cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s GROUP BY category", (DEFAULT_USER_ID, date_pattern,))
            spending = {r[0]: r[1] for r in await cur.fetchall()}
            
        alerts = []
        for cat, budget in budgets.items():
            spent = spending.get(cat, 0.0)
            if spent > budget:
                alerts.append({
                    "category": cat,
                    "budget": budget,
                    "spent": spent,
                    "alert": "Budget exceeded"
                })
        return alerts
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def check_budget_near_limit(month: int, year: int, threshold: float = 0.8) -> list:
    '''Check if spending is near the budget limit (>= threshold * budget).'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
            cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s GROUP BY category", (DEFAULT_USER_ID, date_pattern,))
            spending = {r[0]: r[1] for r in await cur.fetchall()}
            
        alerts = []
        for cat, budget in budgets.items():
            spent = spending.get(cat, 0.0)
            if budget > 0 and spent >= (threshold * budget):
                alerts.append({
                    "category": cat,
                    "budget": budget,
                    "spent": spent,
                    "usage_percent": round((spent / budget) * 100, 2),
                    "alert": "Budget almost reached"
                })
        return alerts
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def detect_high_spending(start_date: str, end_date: str) -> list:
    '''Identify categories where spending is unusually high (e.g. greater than average category spending).'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT category, SUM(amount) as total_spent
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                GROUP BY category
            """, (DEFAULT_USER_ID, start_date, end_date))
            rows = await cur.fetchall()
            
        categories_spending = [{"category": r[0], "spent": r[1]} for r in rows]
        if not categories_spending:
            return []
            
        total_spending = sum(item["spent"] for item in categories_spending)
        avg_spending = total_spending / len(categories_spending)
        
        alerts = []
        for item in categories_spending:
            if item["spent"] > avg_spending:
                alerts.append({
                    "category": item["category"],
                    "spent": item["spent"],
                    "avg_spending": round(avg_spending, 2),
                    "alert": "High spending detected"
                })
        return alerts
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def check_daily_spending_alert(date: str, limit: float) -> dict:
    '''Check if total spending for a specific day exceeds the given limit.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date = %s", (DEFAULT_USER_ID, date,))
            row = await cur.fetchone()
            spent = row[0] if row and row[0] is not None else 0.0
            
        if spent > limit:
            return {
                "date": date,
                "spent": spent,
                "limit": limit,
                "alert": "Daily spending limit exceeded"
            }
        return {}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def check_monthly_overspending(month: int, year: int) -> dict:
    '''Check if total expenses for the month exceed the salary for that month.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            if not row:
                return {}
            salary = row[0]
            
            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern,))
            row = await cur.fetchone()
            spent = row[0] if row and row[0] is not None else 0.0
            
        if spent > salary:
            return {
                "salary": salary,
                "expenses": spent,
                "alert": "Monthly overspending detected"
            }
        return {}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def set_savings_goal(goal_name: str, target_amount: float, target_date: str) -> dict:
    '''Set a new savings goal.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            await db.execute(
                "INSERT INTO savings_goal(user_id, goal_name, target_amount, target_date, created_at) VALUES(%s, %s, %s, %s, now())",
                (DEFAULT_USER_ID, goal_name, target_amount, target_date)
            )
            await db.commit()
        return {
            "status": "ok",
            "goal_name": goal_name,
            "target_amount": target_amount,
            "target_date": target_date
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_savings_progress(month: int, year: int) -> dict:
    '''Calculate savings progress for a specific month (Salary - Expenses).'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0

            date_pattern = f"{year}-{month:02d}-%"
            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s", (DEFAULT_USER_ID, date_pattern,))
            row = await cur.fetchone()
            expenses = row[0] if row and row[0] is not None else 0.0

        return {
            "month": month,
            "year": year,
            "salary": float(salary),
            "expenses": float(expenses),
            "saved": float(salary - expenses)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def get_monthly_savings(year: int) -> list:
    '''Return savings for each month in a given year.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            # Get salary for each month
            cur = await db.execute("SELECT month, salary_amount FROM salary WHERE user_id = %s AND year = %s", (DEFAULT_USER_ID, year,))
            salaries = {r[0]: r[1] for r in await cur.fetchall()}

            # Get expenses for each month
            year_str = str(year)
            cur = await db.execute("""
                SELECT cast(substring(date from 6 for 2) as integer) as month, SUM(amount)
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY month
            """, (DEFAULT_USER_ID, year_str,))
            expenses_dict = {r[0]: r[1] for r in await cur.fetchall()}

        all_months = set(salaries.keys()).union(set(expenses_dict.keys()))
        result = []
        for m in sorted(all_months):
            s = salaries.get(m, 0.0)
            e = expenses_dict.get(m, 0.0)
            result.append({
                "month": m,
                "saved": float(s - e)
            })
        return result
    except Exception as e:
        return [{"status": "error", "message": str(e)}]

@mcp.tool()
async def get_total_saved_money() -> dict:
    '''Calculate total savings across all months (Total Salary - Total Expenses).'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT SUM(salary_amount) FROM salary WHERE user_id = %s", (DEFAULT_USER_ID,))
            row = await cur.fetchone()
            total_salary = row[0] if row and row[0] is not None else 0.0

            cur = await db.execute("SELECT SUM(amount) FROM expenses WHERE user_id = %s", (DEFAULT_USER_ID,))
            row = await cur.fetchone()
            total_expenses = row[0] if row and row[0] is not None else 0.0

        return {
            "total_saved": float(total_salary - total_expenses)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def suggest_savings_amount(month: int, year: int) -> dict:
    '''Suggest a savings amount for a specific month (e.g., 20% of salary).'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT salary_amount FROM salary WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            row = await cur.fetchone()
            salary = row[0] if row else 0.0

        return {
            "salary": float(salary),
            "recommended_savings": float(salary * 0.20)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def generate_monthly_spending_chart(year: int) -> dict:
    '''Generate a bar chart showing monthly expenses.'''
    try:
        year_str = str(year)
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT substring(date from 6 for 2) as month, SUM(amount) as amount
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY month
                ORDER BY month ASC
            """, (DEFAULT_USER_ID, year_str,))
            rows = await cur.fetchall()
            
        month_names = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
            "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }
        
        data = []
        for r in rows:
            data.append({"month": month_names.get(r[0], r[0]), "amount": float(r[1])})
            
        return {
            "chart_type": "bar",
            "title": "Monthly Spending",
            "data": data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def generate_category_pie_chart(start_date: str, end_date: str) -> dict:
    '''Generate a pie chart showing spending distribution.'''
    try:
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT category, SUM(amount) as amount
                FROM expenses
                WHERE user_id = %s AND date BETWEEN %s AND %s
                GROUP BY category
                ORDER BY amount DESC
            """, (DEFAULT_USER_ID, start_date, end_date))
            rows = await cur.fetchall()
            
        categories = []
        values = []
        for r in rows:
            categories.append(r[0])
            values.append(float(r[1]))
            
        return {
            "chart_type": "pie",
            "categories": categories,
            "values": values
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def generate_expense_trend_graph(year: int) -> dict:
    '''Plot a line graph showing spending trend over time.'''
    try:
        year_str = str(year)
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("""
                SELECT substring(date from 6 for 2) as month, SUM(amount) as amount
                FROM expenses
                WHERE user_id = %s AND substring(date from 1 for 4) = %s
                GROUP BY month
                ORDER BY month ASC
            """, (DEFAULT_USER_ID, year_str,))
            rows = await cur.fetchall()
            
        month_names = {
            "01": "Jan", "02": "Feb", "03": "Mar", "04": "Apr", "05": "May", "06": "Jun",
            "07": "Jul", "08": "Aug", "09": "Sep", "10": "Oct", "11": "Nov", "12": "Dec"
        }
        
        data = []
        for r in rows:
            data.append({"month": month_names.get(r[0], r[0]), "amount": float(r[1])})
            
        return {
            "chart_type": "line",
            "title": "Expense Trend",
            "data": data
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@mcp.tool()
async def generate_budget_vs_spending_chart(month: int, year: int) -> dict:
    '''Generate a bar chart comparing budget vs actual spending.'''
    try:
        date_pattern = f"{year}-{month:02d}-%"
        async with await psycopg.AsyncConnection.connect(DB_URL) as db:
            cur = await db.execute("SELECT category, budget_amount FROM category_budget WHERE user_id = %s AND month = %s AND year = %s", (DEFAULT_USER_ID, month, year))
            budgets = {r[0]: r[1] for r in await cur.fetchall()}
            
            cur = await db.execute("SELECT category, SUM(amount) FROM expenses WHERE user_id = %s AND date LIKE %s GROUP BY category", (DEFAULT_USER_ID, date_pattern,))
            spending = {r[0]: r[1] for r in await cur.fetchall()}
            
        categories = []
        budget_values = []
        spent_values = []
        
        all_categories = sorted(list(set(budgets.keys()).union(set(spending.keys()))))
        for cat in all_categories:
            categories.append(cat)
            budget_values.append(float(budgets.get(cat, 0.0)))
            spent_values.append(float(spending.get(cat, 0.0)))
            
        return {
            "chart_type": "bar",
            "categories": categories,
            "budget": budget_values,
            "spent": spent_values
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
