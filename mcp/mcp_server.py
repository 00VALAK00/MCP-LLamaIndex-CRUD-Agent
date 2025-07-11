from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2 import Error
import os 
from pathlib import Path
import uvicorn
# from dotenv import load_dotenv

# Load environment variables
env_path = Path.cwd() / ".env"
# if env_path.exists():
#     load_dotenv(dotenv_path=env_path)

import logging
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel(logging.INFO)

DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "testdb")
DB_USER = os.environ.get("DB_USER", "postgres")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "password")

mcp = FastMCP("sql-mcp-server")

def establish_connection():
    """Connects to the PostgreSQL database and returns the connection object."""
    conn = None
    try:
        # Establish the connection
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        logger.info("Connection to PostgreSQL DB successful!")
        return conn
    

    except Error as e:
        print(f"Error connecting to PostgreSQL DB: {e}")
        return None
    

@mcp.tool(description="creates a new table in the database")
def create_table(table_name: str):
    conn = establish_connection()
    if not conn:
        logger.error("Failed to establish database connection")
        return False
    
    cursor = conn.cursor()
    try:
        # IF NOT EXISTS prevents error if table already exists
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL
        );
        """
        cursor.execute(create_table_query)
        conn.commit() 
        logger.info(f"Table '{table_name}' created successfully.")

    except Error as e:
        # Rollback in case of error
        conn.rollback()
        logger.error(f"Error creating table 'customers': {e}")
    finally:
        # Always close the cursor
        cursor.close()
    
@mcp.tool(description="adds new customers to the database using the SQL Insert function")
def insert_data(query: str):
    """
    Args:
        query (str): SQL INSERT query following this format:
            INSERT INTO customers (name, email)
            VALUES ('John Doe', 'john@example.com')
        
    Schema:
        - name: Text field (required)
        - email: Text field (required)
        Note: 'id' field is auto-generated
    
    Returns:
        bool: True if data was added successfully, False otherwise
    """
    conn = establish_connection()
    if not conn:
        logger.error("Failed to establish database connection")
        return False
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        conn.commit()
        logger.info("Data inserted successfully")
        return True
        
    except Error as e:
        conn.rollback()
        logger.error(f"Error inserting data: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="retrieves data from the database using SQL SELECT queries")
def get_data(query: str):
    """
    Args:
        query (str): SQL SELECT query following this format:
            SELECT * FROM customers
            SELECT name, email FROM customers WHERE name = 'John Doe'
    
    Returns:
        list: List of tuples containing the query results, or empty list if error
    """
    conn = establish_connection()
    if not conn:
        logger.error("Failed to establish database connection")
        return []
    
    cursor = conn.cursor()
    
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        logger.info(f"Retrieved {len(results)} records successfully")
        return results
        
    except Error as e:
        logger.error(f"Error retrieving data: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def main():
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()