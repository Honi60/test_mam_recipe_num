# Rental Receipt Generator

A comprehensive PyQt5-based application for generating and managing rental receipts with Hebrew language support. This system helps property owners create professional PDF receipts, manage customer information, recreate receipts, and export data for authority reporting.

## Features

### 🧾 **Receipt Generation**
- Generate professional PDF receipts with custom templates
- Full Hebrew text support with proper RTL rendering
- Automatic receipt numbering system
- Digital signature integration
- Customizable payment method descriptions

### 👥 **Customer Management**
- Add, edit, and delete customer information
- Store customer-specific save folders and preferences
- Import/export customer data in JSON format
- Search and filter customer records

### 🔄 **Receipt Recreation**
- Recreate receipts from historical records
- View receipt generation history
- Duplicate receipts for corrections or reprints
- Maintain audit trail of all receipt operations

### 📊 **Excel Export**
- Export receipt data for authority reporting
- Generate periodic financial summaries
- Customizable export formats
- Automated data aggregation

## Project Structure

```
reciptGen/
├── main_qt.py                 # Application entry point
├── config/
│   └── paths.py              # Configuration and path management
├── logic/
│   ├── receiptGen.py         # PDF generation logic
│   └── mamAPI.py            # Business logic API
├── QtGUI/
│   ├── main_qt.py            # Main application window
│   ├── receiptGenGUI_qt.py   # Receipt generation interface
│   ├── new_customer_qt.py    # Customer management interface
│   ├── recrate_receipt_qt.py # Receipt recreation interface
│   └── to_excel_qt.py        # Excel export interface
├── utilities/                # Helper scripts and tools
├── resources/               # Application resources
│   ├── fonts/              # Hebrew fonts (Alef family)
│   ├── templates/          # SVG receipt templates
│   ├── images/             # Signatures and icons
│   └── icons/              # Application icons
├── Data/                   # Data files and exports
└── tests/                  # Unit tests
```

## Installation

### Prerequisites
- Python 3.7 or higher
- PyQt5
- ReportLab
- svglib
- python-bidi
- pdfplumber (for utilities)

### Setup Instructions

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd reciptGen
   ```

2. **Install dependencies**
   ```bash
   pip install PyQt5 ReportLab svglib python-bidi pdfplumber
   ```

3. **Configure paths**
   - Edit `config/paths.py` to set your data directories
   - Set `USE_SIMULATION = False` for production use
   - Ensure all resource files are in place

4. **Prepare resources**
   - Place Alef fonts in `resources/fonts/`
   - Add receipt template SVG to `resources/templates/`
   - Add signature image to `resources/images/`

5. **Create data directories**
   ```bash
   # The application will create these automatically
   mkdir -p "E:\My Drive\Rentals\RentalsDB\History"
   ```

## Usage

### Launching the Application
```bash
python main_qt.py
```

### Mode Configuration
The application supports two modes:

- **Simulation Mode** (`USE_SIMULATION = True`)
  - Uses test data directory: `E:\simulation_rentals`
  - Safe for development and testing
  
- **Production Mode** (`USE_SIMULATION = False`)
  - Uses live data directory: `E:\My Drive\Rentals`
  - For actual receipt generation

### Main Interface

The application features a tabbed interface with four main sections:

#### 1. Generate Receipt Tab
- **Select Customer**: Choose from loaded customer list
- **Fill Details**: Enter payment information, dates, descriptions
- **Preview**: Shows receipt layout before generation
- **Generate**: Creates PDF receipt with automatic numbering
- **Save Location**: Configurable per customer or global

#### 2. Customers Tab
- **Customer List**: Browse all customers
- **Add/Edit**: Modify customer information
- **Save Folders**: Set individual save locations per customer
- **Import/Export**: Manage customer database

#### 3. Recreate Receipt Tab
- **History Browser**: View previous receipt generations
- **Search**: Find specific receipts by date or customer
- **Recreate**: Regenerate receipts with original data
- **Audit Trail**: Track all receipt modifications

#### 4. Export to Excel Tab
- **Date Range**: Select reporting period
- **Data Selection**: Choose which fields to export
- **Format Options**: Customize Excel layout
- **Generate**: Create authority-ready reports

## Configuration

### Path Configuration (`config/paths.py`)

```python
# Set operating mode
USE_SIMULATION = False  # True for testing, False for production

# Data directories (automatically configured based on mode)
RECIEPT_ROOT = "E:\\My Drive\\Rentals"  # Main data directory
DB_DIR = "E:\\My Drive\\Rentals\\RentalsDB"  # Database directory
```

### Resource Files

- **Fonts**: `Alef-Regular.ttf`, `Alef-Bold.ttf` for Hebrew text
- **Templates**: `receipt_template_TP.svg` for receipt layout
- **Images**: `HoniSigneture.jpg` for digital signature
- **Icons**: `receiptCreat.ico` for application icon

## Data Management

### Customer Data Format
```json
{
  "CustomerName": {
    "customer": "שם לקוח",
    "discription": "תיאור תשלום",
    "payment": "1000",
    "bankAccount": "12345",
    "BankNumber": "012",
    "CheckNumber": "",
    "save_folder": "customer_folder_path"
  }
}
```

### History Records
Each receipt generation creates a history record:
```json
{
  "receipt_number": "12345",
  "customer": "CustomerName",
  "date": "2024-01-15",
  "amount": "1000",
  "description": "שכירות ינואר 2024",
  "filename": "CustomerName_20240115_12345.pdf",
  "timestamp": "2024-01-15T10:30:00"
}
```

## Utilities

The `utilities/` directory contains helpful scripts:

- **`pdf_viewer_gui.py`**: GUI for viewing and managing PDF receipts
- **`extract_receipt_numbers.py`**: Extract receipt numbers from PDF files
- **`list_customer_receipt_folders.py`**: List all customer receipt folders
- **`compare_receipt_lists.py`**: Compare different receipt lists
- **`simple_pdf_counter.py`**: Count PDF files in directories

## Troubleshooting

### Common Issues

1. **Font Loading Errors**
   - Ensure Alef fonts are in `resources/fonts/`
   - Check font file permissions
   - Application falls back to Helvetica if fonts unavailable

2. **Path Configuration Issues**
   - Verify `USE_SIMULATION` setting matches your setup
   - Ensure data directories exist and are writable
   - Check file permissions on database directory

3. **PDF Generation Failures**
   - Verify template SVG exists and is readable
   - Check signature image file
   - Ensure output directory is writable

4. **Hebrew Text Issues**
   - Ensure text is properly encoded (UTF-8)
   - Check bidi algorithm is working
   - Verify font supports Hebrew characters

### Debug Mode

Enable debug output by checking console messages when running the application. Most operations print status information to the console.

## Development

### Adding New Features

1. **GUI Components**: Add new tabs to `QtGUI/main_qt.py`
2. **Business Logic**: Add functions to `logic/` directory
3. **Configuration**: Update `config/paths.py` for new paths
4. **Resources**: Add new assets to appropriate `resources/` subdirectory

### Testing

Run tests from the `tests/` directory:
```bash
python -m pytest tests/
```

### Code Style

The project follows PEP 8 guidelines with additional considerations:
- Use meaningful variable names
- Add docstrings for complex functions
- Handle exceptions gracefully
- Support both simulation and production modes

## License

This project is developed for rental property management and receipt generation. Please ensure compliance with local financial regulations when using this software for official receipts.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review error messages in the console
3. Verify all resource files are properly configured
4. Test with simulation mode first before production use

---

**Note**: This application was originally developed with GitHub Copilot and is being enhanced with Windsurf for improved code quality and maintainability.
