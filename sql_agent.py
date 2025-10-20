import sqlite3
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

def get_schema():
    return """
    Table: employees
    Columns:
    - id (INTEGER PRIMARY KEY)
    - name (TEXT)
    - department (TEXT)
    - salary (REAL)
 
    Table: departments
    Columns:
    - id (INTEGER PRIMARY KEY)
    - name (TEXT)
    - budget (REAL)
    """


def generate_sql(question: str, llm: ChatOpenAI) -> str:
    
    # Create the system message with the schema
    system_content = f"""You are a SQL expert. Use this schema:
{get_schema()}
Return ONLY the SQL query without any explanation or markdown formatting."""
    
    # Create the messages list
    messages = [
        SystemMessage(content=system_content),
        HumanMessage(content=f"Generate SQL for: {question}")
    ]
    
    # Use the 'llm.invoke()' method from LangChain
    response = llm.invoke(messages)
    
    # The response object is different; get the content
    sql = response.content.strip()
    
    # Cleaning logic
    sql = sql.replace('```sql', '').replace('```SQL', '').replace('```', '')
    sql_lines = [line.strip() for line in sql.split('\n') if line.strip()]
    sql = ' '.join(sql_lines)
    
    return sql

def validate_sql(sql):
    # Basic safety checks
    sql_lower = sql.lower()
    if any(word in sql_lower for word in ['drop', 'delete', 'update', 'insert']):
        raise ValueError("Only SELECT queries are allowed")
    return sql

def execute_query(sql):
    sql = validate_sql(sql)
    # Connects to the database file
    conn = sqlite3.connect('company.db')
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        return results
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        conn.close()

def format_results(results):
    if not isinstance(results, list):
        return str(results)
    if not results:
        return "No results found"
    
    # If it's a single column result
    if len(results[0]) == 1:
        return "\n".join([str(row[0]) for row in results])
    
    # For multiple columns
    if isinstance(results[0], tuple):
        formatted_rows = []
        for row in results:
            row_items = []
            for item in row:
                if isinstance(item, float):
                    row_items.append(f"${item:,.2f}" if "salary" in str(row) or "budget" in str(row) else f"{item:.2f}")
                else:
                    row_items.append(str(item))
            formatted_rows.append("\t".join(row_items))
        return "\n".join(formatted_rows)
        
    return "\n".join([str(row) for row in results])

def query_agent(question: str, llm: ChatOpenAI) -> str:
    try:
        # Generate SQL
        sql = generate_sql(question, llm)
        print(f"Generated SQL: {sql}\n")
        
        # Execute and format results
        results = execute_query(sql)
        return format_results(results)
    except Exception as e:
        return f"Error: {str(e)}"
