# Iden Challenge Automation Script

A sophisticated Python automation script designed to solve the Iden Challenge by efficiently extracting product data from a web application. This script combines robust authentication, intelligent session management, and advanced table extraction techniques to handle large datasets with virtualized tables.

## **Overview**

The Iden Challenge Automation Script is a production-ready solution that:
- **Authenticates** with the Iden hiring platform
- **Navigates** through a hidden path to access product data
- **Extracts** all product information using infinite scroll strategy
- **Exports** data to structured JSON format
- **Manages** sessions intelligently to avoid repeated logins

## **Key Features**

### **Smart Session Management**
- **Automatic Session Reuse**: Detects and reuses existing sessions to skip authentication
- **Multi-Storage Persistence**: Saves cookies, localStorage, and sessionStorage separately
- **Session Validation**: Automatically detects expired sessions and forces re-authentication
- **Graceful Fallback**: Handles session failures without crashing

### **Robust Authentication**
- **Environment-Based Credentials**: Secure credential management via `.env` files
- **Multi-Auth Strategy**: Supports both fresh login and session restoration
- **Error Handling**: Comprehensive error handling for authentication failures
- **Session Persistence**: Saves authentication state for future runs

### **Advanced Data Extraction**
- **Infinite Scroll Support**: Handles virtualized tables with dynamic loading
- **Smart Scrolling**: Automatically detects scrollable containers and optimizes scrolling
- **Progress Tracking**: Real-time progress updates during extraction
- **Data Validation**: Ensures data integrity with proper error handling

### **Professional CLI Interface**
- **Command Line Arguments**: Full CLI support with help documentation
- **Configurable Parameters**: Customizable target counts, output files, and headless mode
- **Version Control**: Built-in versioning and help system
- **Performance Metrics**: Execution time and throughput reporting

##  **Requirements**

### **System Requirements**
- Python 3.7+
- Windows/macOS/Linux
- 4GB+ RAM (for large datasets)
- Stable internet connection

### **Python Dependencies**
```
playwright>=1.40.0
python-dotenv>=1.0.0
```

### **Browser Requirements**
- Chromium browser (automatically managed by Playwright)
- No manual browser installation required

## **Installation**

### **1. Clone or Download**
```bash
git clone <repository-url>
cd idenchallenge
```

### **2. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **3. Install Playwright Browsers**
```bash
playwright install chromium
```

### **4. Set Up Environment Variables**
Create a `.env` file in the project directory:
```bash
# .env file
IDEN_USERNAME=your_email@example.com
IDEN_PASSWORD=your_password_here
```

**Alternative**: Set environment variables in your shell:
```bash
export IDEN_USERNAME=your_email@example.com
export IDEN_PASSWORD=your_password_here
```

## **Usage**

### **Basic Usage**
```bash
python iden_unified.py
```

### **Advanced Options**
```bash
# Run in headless mode (no browser GUI)
python iden_unified.py --headless

# Custom target count
python iden_unified.py --target-count 1000

# Custom output file
python iden_unified.py --output products.json

# Combine options
python iden_unified.py --headless --target-count 500 --output data.json

# Show help
python iden_unified.py --help

# Show version
python iden_unified.py --version
```

### **Command Line Arguments**

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--headless` | flag | False | Run browser without GUI |
| `--target-count` | int | 2332 | Target number of products to extract |
| `--output` | string | product_data.json | Output JSON filename |
| `--version` | flag | - | Show version information |
| `--help` | flag | - | Show help message |

## **How It Works**

### **1. Session Management Flow**
```
Start → Check for existing session files
  ↓
If session exists → Validate session → Reuse if valid
  ↓
If no session → Authenticate → Save new session
  ↓
Continue with authenticated session
```

### **2. Navigation Strategy**
The script follows a specific button sequence to access the product data:
1. **Start Journey** - Initiates the challenge
2. **Continue Search** - Proceeds to next step
3. **Inventory Section** - Accesses the inventory area
4. **Show Product Table** - Attempts to display the table (with fallback)

**Note**: The "Show Product Table" button may not exist on all pages, so the script gracefully handles its absence.

### **3. Data Extraction Process**
```
Wait for table → Extract headers → Start infinite scroll
  ↓
Scroll until target count or stagnation → Extract row data
  ↓
Clean and validate data → Export to JSON
```

### **4. Infinite Scroll Algorithm**
- **Smart Container Detection**: Automatically finds scrollable parent elements
- **Progress Monitoring**: Tracks row count growth every 100 rows
- **Stagnation Detection**: Stops when no new rows appear for 3 consecutive attempts
- **Performance Optimization**: Uses efficient DOM manipulation for large datasets

## **Output Format**

### **JSON Structure**
```json
{
  "extraction_timestamp": "2024-01-01 12:00:00",
  "total_products": 2332,
  "target_products": 2332,
  "products": [
    {
      "Column_1": "Product Name",
      "Column_2": "Price",
      "Column_3": "Category",
      // ... additional columns
    }
  ]
}
```

### **Data Quality Features**
- **Header Detection**: Automatically extracts table headers or generates fallback names
- **Row Padding**: Handles incomplete rows by padding with `null` values
- **Data Cleaning**: Ensures all values are JSON-serializable
- **Error Recovery**: Continues extraction even if individual rows fail

## **Session Management Details**

### **Session Files Created**
1. **`session.json`** - Playwright cookies and storage state
2. **`session_storage.json`** - Browser sessionStorage (contains auth tokens)
3. **`local_storage.json`** - Browser localStorage (backup storage)

### **Session Restoration Process**
1. **File Validation**: Checks if session files exist and contain valid data
2. **Browser Context**: Creates fresh browser context without previous state
3. **Storage Injection**: Manually injects saved sessionStorage before navigation
4. **Session Validation**: Verifies session is still valid on the challenge page

### **Session Cleanup**
- **Invalid Session Detection**: Automatically removes expired session files
- **Force Fresh Login**: Cleans up and forces re-authentication when needed
- **Error Recovery**: Handles session corruption gracefully

## **Error Handling**

### **Authentication Errors**
- **Missing Credentials**: Clear error messages with setup instructions
- **Login Failures**: Detailed logging and graceful failure handling
- **Session Expiry**: Automatic detection and cleanup

### **Navigation Errors**
- **Button Not Found**: Graceful fallback for missing navigation elements
- **Page Load Failures**: Timeout handling and retry logic
- **Table Not Found**: Clear error reporting for missing data

### **Data Extraction Errors**
- **Scroll Failures**: Fallback to alternative scrolling methods
- **Row Parsing Errors**: Continues extraction with error logging
- **Memory Issues**: Efficient data processing to handle large datasets

### **Network Errors**
- **Connection Issues**: Automatic retry with exponential backoff
- **Timeout Handling**: Configurable timeouts for different operations
- **Load State Management**: Waits for network idle before proceeding

## **Performance Features**

### **Optimization Techniques**
- **Efficient Scrolling**: Optimized scroll algorithms for virtualized tables
- **Progress Tracking**: Real-time updates every 100 rows extracted
- **Memory Management**: Processes data in chunks to avoid memory issues
- **Performance Metrics**: Reports extraction speed (products/second)

### **Scalability**
- **Large Dataset Support**: Tested with 2000+ product records
- **Configurable Targets**: Adjustable extraction limits
- **Resource Management**: Automatic browser cleanup and resource release

## **Troubleshooting**

### **Common Issues**

#### **"Credentials missing" Error**
```bash
# Solution: Create .env file
echo "IDEN_USERNAME=your_email@example.com" > .env
echo "IDEN_PASSWORD=your_password" >> .env
```

#### **"Session invalid" Error**
```bash
# Solution: Delete session files and re-run
rm session.json session_storage.json local_storage.json
python iden_unified.py
```

#### **"Table not found" Error**
- Ensure you're on the correct challenge page
- Check if the navigation path has changed
- Verify internet connection stability

#### **Browser Launch Issues**
```bash
# Solution: Reinstall Playwright browsers
playwright install --force chromium
```

### **Debug Mode**
The script includes comprehensive logging:
```bash
# Check logs for detailed information
python iden_unified.py 2>&1 | tee automation.log
```

### **Session Debugging**
```bash
# Check session file contents
cat session_storage.json | jq '.'
cat local_storage.json | jq '.'
```

## **Security Considerations**

### **Credential Management**
- **Environment Variables**: Credentials stored in `.env` files (not in code)
- **Session Security**: Authentication tokens stored locally
- **No Hardcoding**: All sensitive data externalized

### **Data Privacy**
- **Local Processing**: All data processing happens locally
- **No External Transmission**: Data never leaves your machine
- **Session Isolation**: Each run uses isolated browser context

## **Development & Customization**

### **Adding New Navigation Steps**
```python
# Modify the buttons_path in __init__
self.buttons_path = [
    ("button", "Start Journey"),
    ("button", "Continue Search"),
    ("button", "Inventory Section"),
    ("button", "Show Product Table"),
    ("button", "New Step"),  # Add new steps here
]
```

### **Custom Data Processing**
```python
# Override extract_product_data method
def extract_product_data(self, target_count: int = 2332) -> List[Dict]:
    # Custom extraction logic
    pass
```

### **Extending Output Formats**
```python
# Add new export methods
def export_to_csv(self, data: List[Dict]) -> None:
    # CSV export implementation
    pass
```

## **API Reference**

### **Core Methods**

#### **`setup_browser(headless: bool) -> bool`**
Initializes browser and context. Returns `True` if session was reused.

#### **`authenticate() -> bool`**
Performs authentication. Returns `True` on success.

#### **`navigate_hidden_path(page: Page) -> bool`**
Navigates through the challenge path. Returns `True` when table is found.

#### **`extract_product_data(target_count: int) -> List[Dict]`**
Extracts product data. Returns list of product dictionaries.

#### **`export_to_json(data: List[Dict]) -> None`**
Exports data to JSON file.

### **Utility Methods**

#### **`show_session_summary(session_status, session_data)`**
Displays concise session information.

#### **`print_session_info(after: str)`**
Unified session information display.

#### **`show_detailed_session_info()`**
Comprehensive session debugging information.

## **Contributing**

### **Code Style**
- Follow PEP 8 guidelines
- Use type hints for all function parameters
- Include comprehensive docstrings
- Add error handling for all external operations

### **Testing**
- Test with different target counts
- Verify session management scenarios
- Test error handling paths
- Validate output data integrity

## **License**

This script is provided as-is for educational and automation purposes. Use responsibly and in accordance with the target website's terms of service.

## **Acknowledgments**

- **Playwright**: For robust browser automation capabilities
- **Python Community**: For excellent libraries and tools
- **Iden Team**: For providing an interesting automation challenge

---

**Note**: This script is designed for educational purposes and legitimate automation tasks. Always respect website terms of service and rate limits when using automation tools. 