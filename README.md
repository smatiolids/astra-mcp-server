# Astra MCP Server

A Model Context Protocol (MCP) server for interacting with Astra DB (DataStax Astra).

## Features

- **Database Operations**: Full CRUD operations for Astra DB collections
- **MCP Integration**: Seamless integration with MCP-compatible clients
- **Comprehensive Logging**: Detailed logging system for debugging and monitoring
- **Environment Configuration**: Flexible configuration through environment variables

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables (see Configuration section)

## Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Astra DB Configuration
ASTRA_DB_APPLICATION_TOKEN=your_astra_db_token
ASTRA_DB_API_ENDPOINT=your_astra_db_endpoint

# Logging Configuration (optional)
LOG_LEVEL=INFO
LOG_FILE=logs/astra_mcp_server.log
```

### Logging Configuration

The project includes a comprehensive logging system with the following features:

#### Log Levels
- `DEBUG`: Detailed information for debugging
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially problematic situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical error messages that may prevent the program from running

#### Log Output
- **Console Output**: All log messages are displayed in the console
- **File Output**: Log messages can be written to files (optional)
- **Structured Format**: Timestamp, logger name, level, and message

#### Usage Examples

```python
from logger import get_logger

# Basic logger
logger = get_logger("my_module")
logger.info("Application started")

# Custom configuration
custom_logger = get_logger(
    name="custom",
    level="DEBUG",
    log_file="logs/custom.log"
)

# Environment-based configuration
# Set LOG_LEVEL and LOG_FILE environment variables
env_logger = get_logger("environment")
```

#### Logger Configuration Options

```python
from logger import LoggerConfig

config = LoggerConfig(
    name="astra_mcp_server",
    level="INFO",
    log_file="logs/server.log",
    format_string="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = config.setup_logger()
```

## Usage

### Starting the Server

```bash
python server.py
```

The server will start on port 5150 with SSE transport.

### Database Operations

The `AstraDBManager` class provides the following operations:

- `find_documents()`: Query documents from collections
- `insert_document()`: Insert new documents
- `update_document()`: Update existing documents
- `delete_document()`: Delete documents
- `list_collections()`: List all collections
- `get_collection_info()`: Get collection metadata

All operations include comprehensive logging for debugging and monitoring.

### Example Usage

```python
from database import AstraDBManager

# Initialize database manager
db_manager = AstraDBManager()

# List collections
collections = db_manager.list_collections()
print(collections)

# Insert a document
document = {"name": "John", "age": 30}
result = db_manager.insert_document(document, "users")
print(result)
```

## Logging Examples

Run the example logging script to see different logging scenarios:

```bash
python example_logging.py
```

This will demonstrate:
- Basic logger usage
- Custom logger configuration
- Database operations with logging
- Environment-based logging
- Different log levels

## Project Structure

```
astra-mcp-server/
├── server.py              # Main server entry point
├── database.py            # Database operations and AstraDBManager
├── load_tools.py          # MCP tool loading
├── logger.py              # Logging configuration and utilities
├── example_logging.py     # Example logging usage
├── README.md              # This file
└── requirements.txt       # Python dependencies
```

## Development

### Adding New Tools

1. Create your tool function in `load_tools.py`
2. Add it to the `load_all_tools()` method
3. The logger will automatically track tool loading

### Adding Logging to New Modules

1. Import the logger:
   ```python
   from logger import get_logger
   ```

2. Create a logger instance:
   ```python
   logger = get_logger("your_module_name")
   ```

3. Use appropriate log levels:
   ```python
   logger.debug("Debug information")
   logger.info("General information")
   logger.warning("Warning message")
   logger.error("Error message")
   logger.critical("Critical error")
   ```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**: Check your Astra DB credentials in the `.env` file
2. **Log File Not Created**: Ensure the logs directory exists or the logger will create it
3. **Permission Errors**: Check file permissions for log file locations

### Debug Mode

To enable debug logging, set the environment variable:

```bash
export LOG_LEVEL=DEBUG
```

Or in your `.env` file:

```env
LOG_LEVEL=DEBUG
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add appropriate logging to your changes
4. Submit a pull request

## License

[Add your license information here]
