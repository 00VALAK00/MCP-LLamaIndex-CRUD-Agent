# AutoGen LlamaIndex Ollama Agent with MCP Tools

This project demonstrates how to create an MCP server and an AI agent using LlamaIndex and Ollama that can interact with a PostgreSQL database through MCP (Model Context Protocol).

## Features

- **MCP-Compatible FunctionAgent**: Uses LlamaIndex's FunctionAgent with proper MCP protocol integration
- **Dynamic Tool Discovery**: Automatically discovers MCP tools from the server
- **PostgreSQL Database Tools**: MCP server with database operations (create_table, insert_data, get_data)
- **Ollama Integration**: Uses local Ollama LLM for processing
- **Interactive Interface**: Command-line interface for database operations
- **Docker Support**: PostgreSQL database containerized with Docker Compose

## Prerequisites

- **PostgreSQL Database**: Running instance (or use Docker)
- **Ollama**: Install and run with llama3.1 model
- **Python 3.12+**: Required for the project
- **Docker & Docker Compose**: For running PostgreSQL database

## Quick Start

### 1. Install Dependencies

```bash
pip install -e .
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=customers
DB_USER=postgres
DB_PASSWORD=postgres
```

### 3. Start Services

```bash
# Start PostgreSQL database
docker-compose up -d db

# Start Ollama (in a separate terminal)
ollama pull llama3.1:latest
ollama serve
```

### 4. Run the Agent

```bash
python scripts/agent.py
```

## Usage Example

```
Server is running...
Agent is ready...
What would you like to do? Create a customers table
Calling tool create_table with kwargs {'table_name': 'customers'}
✅ Table 'customers' created successfully.

What would you like to do? Add a new customer named John Doe with email john@example.com
Calling tool insert_data with kwargs {'query': "INSERT INTO customers (name, email) VALUES ('John Doe', 'john@example.com')"}
✅ Data inserted successfully

What would you like to do? Show me all customers
Calling tool get_data with kwargs {'query': 'SELECT * FROM customers'}
📋 Customers:
ID: 1, Name: John Doe, Email: john@example.com
```

## Architecture

```
┌─────────────────┐    MCP Protocol    ┌─────────────────┐
│  FunctionAgent  │ ◄────────────────► │   MCP Server    │
│   (LlamaIndex)  │                    │  (PostgreSQL)   │
└─────────────────┘                    └─────────────────┘
         │                                       │
         │ Tool Calls                            │
         ▼                                       ▼
┌─────────────────┐                    ┌─────────────────┐
│  Ollama LLM     │                    │  PostgreSQL DB  │
└─────────────────┘                    └─────────────────┘
```

## MCP Tools

- **`create_table`**: Creates new tables in the database
- **`insert_data`**: Adds new data to database tables  
- **`get_data`**: Retrieves data from database tables

## Dependencies

- **llama-index-llms-ollama**: Ollama LLM integration
- **mcp[cli]**: Model Context Protocol implementation
- **ollama**: Ollama client library
- **psycopg2**: PostgreSQL adapter
- **pydantic-settings**: Settings management
- **python-dotenv**: Environment variable loading

## Development

### Adding New MCP Tools

1. Add new `@mcp.tool` decorated functions to `mcp/mcp_server.py`
2. The agent will automatically discover new tools
3. No changes needed to the agent code

### Extending the Agent

1. Modify the `get_agent()` function in `scripts/agent.py`
2. Add new methods for custom functionality
3. Update the interactive chat loop as needed

## License

This project is open source and available under the MIT License.
