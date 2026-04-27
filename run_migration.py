"""
Migration script to add missing columns to payroll_runs table.
"""
import sys
import os

# Add the app directory to path
sys.path.insert(0, '.')

# Import Flask app
from app import app

# Use the app context
with app.app_context():
    from models.db import get_db
    from mysql.connector import Error
    
    try:
        # Get a connection
        db = get_db()
        cur = db.cursor()
        
        # Check current columns in payroll_runs
        cur.execute("DESCRIBE payroll_runs")
        columns = {row[0] for row in cur.fetchall()}
        
        # Write to file
        with open('migration_output.txt', 'w') as f:
            f.write(f"Current columns: {columns}\n")
            
            # Columns to add
            new_columns = [
                ("overtime_hours", "DECIMAL(6,2) DEFAULT 0"),
                ("overtime_amount", "DECIMAL(15,2) DEFAULT 0"),
                ("prorated_salary", "DECIMAL(15,2) DEFAULT 0"),
                ("housing_allowance", "DECIMAL(15,2) DEFAULT 0"),
                ("transport_allowance", "DECIMAL(15,2) DEFAULT 0"),
                ("meal_allowance", "DECIMAL(15,2) DEFAULT 0"),
                ("performance_bonus", "DECIMAL(15,2) DEFAULT 0"),
            ]
            
            for col_name, col_def in new_columns:
                if col_name not in columns:
                    try:
                        cur.execute(f"ALTER TABLE payroll_runs ADD COLUMN {col_name} {col_def}")
                        db.commit()
                        f.write(f"Added column: {col_name}\n")
                    except Error as e:
                        f.write(f"Error adding {col_name}: {e}\n")
                else:
                    f.write(f"Column {col_name} already exists\n")
            
            f.write("Migration complete!\n")
        
        cur.close()
        
    except Exception as e:
        with open('migration_output.txt', 'w') as f:
            f.write(f"Error: {e}\n")
            import traceback
            f.write(traceback.format_exc())