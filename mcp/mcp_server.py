import argparse
import sys
from pathlib import Path

# Add project root to path BEFORE importing config
sys.path.append(str(Path(__file__).parent.parent))

from mcp.server.fastmcp import FastMCP
import psycopg2
from psycopg2 import Error
import os 
from typing import  Optional
from config.settings import DatabaseConfig

import logging
from logging import getLogger

logger = getLogger(__name__)
logger.setLevel(logging.INFO)


mcp = FastMCP("sql-mcp-server")

def establish_connection():
    """Connects to the PostgreSQL database and returns the connection object."""
    conn = None
    db_config = DatabaseConfig.get_config()
    try:
        # Establish the connection
        conn = psycopg2.connect(
            host=db_config["host"],
            port=db_config["port"],
            database=db_config["database"],
            user=db_config["user"],
            password=db_config["password"]
        )
        logger.info("Connection to PostgreSQL DB successful!")
        return conn
    except Error as e:
        logger.error(f"Error connecting to PostgreSQL DB: {e}")
        return None

def format_results(cursor, results):
    """Format query results as a list of dictionaries with column names."""
    if not results:
        return []
    
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in results]

# ==================== CREATE OPERATIONS ====================

@mcp.tool(description="creates a new table in the database with custom schema")
def create_table(table_name: str, schema: str):
    """
    Args:
        table_name (str): Name of the table to create
        columns (str): schema for the table 
    Returns:
        dict: Status message with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:        
        
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} ({schema});
        """
        cursor.execute(create_table_query)
        conn.commit()
        
        return {"success": True, "message": f"Table '{table_name}' created successfully"}
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error creating table: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="inserts a single record into a specified table")
def insert_record(table_name: str, data: str):
    """
    Args:
        table_name (str): Name of the table to insert into
        table_schema (str): schema for the table without a type (you must retrieve this from the get_table_schema tool) e.g: "name, email, age"
        data (str): string, e.g.:
            "John Doe, john@example.com, 30"
    
    Returns:
        dict: Status message with success/failure information and inserted record ID
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:    
        # query to insert the record into the table e.g: INSERT INTO users (name, email, age) VALUES ('John Doe', 'john@example.com', 30)
        insert_query = f"""
        INSERT INTO {table_name} (data)
        RETURNING id;
        """        

        logger.warning(f"Insert query: {insert_query.format(data=data)}")

        cursor.execute(insert_query)
        result = cursor.fetchone()
        if result:
            inserted_id = result[0]
        else:
            inserted_id = None
        conn.commit()
        
        return {
            "success": True, 
            "message": f"Record inserted successfully", 
            "inserted_id": inserted_id
        }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error inserting record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# ==================== READ OPERATIONS ====================

@mcp.tool(description="retrieves all records from a table")
def get_all_records(table_name: str, limit: Optional[int] = 100):
    """
    Args:
        table_name (str): Name of the table to query
        limit (int, optional): Maximum number of records to return (default: 100)
    
    Returns:
        dict: Query results with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        query = f"SELECT * FROM {table_name} LIMIT %s"
        cursor.execute(query, (limit,))
        results = cursor.fetchall()
        
        formatted_results = format_results(cursor, results)
        
        return {
            "success": True,
            "message": f"Retrieved {len(formatted_results)} records",
            "data": formatted_results
        }
        
    except Error as e:
        return {"success": False, "message": f"Error retrieving records: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="finds records by specific criteria")
def find_records(table_name: str, conditions: str):
    """
    Args:
        table_name (str): Name of the table to query
        conditions (str): 
    
    Returns:
        dict: Query results with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:        
        
        query = f"SELECT * FROM {table_name} WHERE {conditions}"
        
        cursor.execute(query)
        results = cursor.fetchall()
        
        formatted_results = format_results(cursor, results)
        
        return {
            "success": True,
            "message": f"Found {len(formatted_results)} matching records",
            "data": formatted_results
        }
        
    except Error as e:
        return {"success": False, "message": f"Error finding records: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="gets a single record by ID")
def get_record_by_id(table_name: str, record_id: int):
    """
    Args:
        table_name (str): Name of the table to query
        record_id (int): ID of the record to retrieve
    
    Returns:
        dict: Record data with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        query = f"SELECT * FROM {table_name} WHERE id = %s"
        cursor.execute(query, (record_id,))
        result = cursor.fetchone()
        
        if result:
            formatted_result = format_results(cursor, [result])[0]
            return {
                "success": True,
                "message": "Record found",
                "data": formatted_result
            }
        else:
            return {
                "success": False,
                "message": f"No record found with ID {record_id}"
            }
        
    except Error as e:
        return {"success": False, "message": f"Error retrieving record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# ==================== UPDATE OPERATIONS ====================

@mcp.tool(description="updates a single record by ID")
def update_record(table_name: str, record_ids: int, set_condition: str):
    """
    Args:
        table_name (str): Name of the table to update
        record_id (int): ID of the record to update
        condition (str): sql like condition to update the record

    eg:
        table_name = "users"
        record_ids = "1,2,3"
        set_condition = "name = 'John', email = 'john@example.com'"
    
    Returns:
        dict: Status message with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
    
        
        update_query = f"""
        UPDATE {table_name} 
        SET {set_condition}
        WHERE id IN ({record_ids})
        RETURNING id;
        """
        
        cursor.execute(update_query)
        updated_record = cursor.fetchall()
        
        if updated_record:
            conn.commit()
            return {
                "success": True,
                "message": f"Records {record_ids} updated successfully"
            }
        else:
            conn.rollback()
            return {
                "success": False,
                "message": f"No records found with ID {record_ids}"
            }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error updating record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()



@mcp.tool(description="updates multiple records by criteria")
def update_records_by_criteria(table_name: str, set_clause: str, where_clause: str):
    """
    Args:
        table_name (str): Name of the table to update
        set_clause (str): sql like set clause to update the records
        where_clause (str): sql like where clause to update the records

    eg:
        table_name = "users"
        set_clause = "name = 'John', email = 'john@example.com'"
        where_clause = "age > 25"
    
    Returns:
        dict: Status message with success/failure information and count of updated records
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        
        update_query = f"""
        UPDATE {table_name} 
        SET {set_clause}
        WHERE {where_clause}
        RETURNING id;
        """
        
        cursor.execute(update_query)
        updated_records = cursor.fetchall()
        
        if updated_records:
            conn.commit()
            return {
                "success": True,
                "message": f"{len(updated_records)} records updated successfully",
                "updated_count": len(updated_records)
            }
        else:
            conn.rollback()
            return {
                "success": False,
                "message": "No records found matching the criteria"
            }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error updating records: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# ==================== DELETE OPERATIONS ====================

@mcp.tool(description="deletes a single record by ID")
def delete_record(table_name: str, record_id: int):
    """
    Args:
        table_name (str): Name of the table to delete from
        record_id (int): ID of the record to delete
    
    Returns:
        dict: Status message with success/failure information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        delete_query = f"""
        DELETE FROM {table_name} 
        WHERE id = %s
        RETURNING id;
        """
        
        cursor.execute(delete_query, (record_id,))
        deleted_record = cursor.fetchone()
        
        if deleted_record:
            conn.commit()
            return {
                "success": True,
                "message": f"Record {record_id} deleted successfully"
            }
        else:
            conn.rollback()
            return {
                "success": False,
                "message": f"No record found with ID {record_id}"
            }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error deleting record: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="deletes multiple records by criteria")
def delete_records_by_criteria(table_name: str, where_clause: str):
    """
    Args:
        table_name (str): Name of the table to delete from
        conditions (str): JSON string with deletion criteria, e.g.:
            '{"name": "John"}' or '{"age": 25, "status": "inactive"}'
    
    Returns:
        dict: Status message with success/failure information and count of deleted records
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        
        delete_query = f"""
        DELETE FROM {table_name} 
        WHERE {where_clause}
        RETURNING id;
        """
        
        cursor.execute(delete_query)
        deleted_records = cursor.fetchall()
        
        conn.commit()
        
        return {
            "success": True,
            "message": f"Deleted {len(deleted_records)} records",
            "deleted_count": len(deleted_records)
        }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error deleting records: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

# ==================== UTILITY OPERATIONS ====================

@mcp.tool(description="gets table schema information")
def get_table_schema(table_name: str):
    """
    Args:
        table_name (str): Name of the table to get schema for
    
    Returns:
        dict: Table schema information
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        query = """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_name = %s AND table_schema = 'public'
        ORDER BY ordinal_position;
        """
        
        cursor.execute(query, (table_name,))
        results = cursor.fetchall()
        
        schema = []
        for row in results:
            schema.append({
                "column_name": row[0],
                "data_type": row[1],
                "is_nullable": row[2],
                "column_default": row[3]
            })
        
        return {
            "success": True,
            "message": f"Schema for table '{table_name}'",
            "schema": schema
        }
        
    except Error as e:
        return {"success": False, "message": f"Error getting schema: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="lists all tables in the database")
def list_tables():
    """
    Returns:
        dict: List of all tables in the database
    """
    conn = establish_connection()
    if not conn:
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
        """
        
        cursor.execute(query)
        results = cursor.fetchall()
        tables = [row[0] for row in results]
        
        return {
            "success": True,
            "message": f"Found {len(tables)} tables",
            "tables": tables
        }
        
    except Error as e:
        return {"success": False, "message": f"Error listing tables: {str(e)}"}
    finally:
        cursor.close()
        conn.close()

@mcp.tool(description="drops a table from the database")
def drop_table(table_name: str):
    """
    Args:
        table_name (str): Name of the table to drop
    """
    conn = establish_connection()
    if not conn:    
        return {"success": False, "message": "Failed to establish database connection"}
    
    cursor = conn.cursor()
    try:
        drop_query = f"""
        DROP TABLE IF EXISTS {table_name};
        """
        
        cursor.execute(drop_query)
        conn.commit()
        
        return {
            "success": True,
            "message": f"Table '{table_name}' dropped successfully"
        }
        
    except Error as e:
        conn.rollback()
        return {"success": False, "message": f"Error dropping table: {str(e)}"}
    finally:
        cursor.close()
        conn.close()



def main():
    """Main function with command line argument support"""
    # Get default database configuration
    db_config = DatabaseConfig.get_config()
    
    parser = argparse.ArgumentParser(description="MCP SQL Server with configurable database connection")
    parser.add_argument("--host", default=db_config["host"], help="Database host")
    parser.add_argument("--port", type=int, default=db_config["port"], help="Database port")
    parser.add_argument("--database", default=db_config["database"], help="Database name")
    parser.add_argument("--user", default=db_config["user"], help="Database user")
    parser.add_argument("--password", default=db_config["password"], help="Database password")
    parser.add_argument("--mcp-host", default="127.0.0.1", help="MCP server host (default: 127.0.0.1)")
    parser.add_argument("--mcp-port", type=int, default=8000, help="MCP server port (default: 8000)")
    
    args = parser.parse_args()

    # Start the MCP server
    mcp.run(transport="sse")

if __name__ == "__main__":
    main()