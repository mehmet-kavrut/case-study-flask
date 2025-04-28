# Data Quality Validator

Data Quality Validator is a powerful, lightweight data quality validation tool built with Flask. It allows users to upload datasets and quickly detect and report data quality issues such as missing values, outliers, data type mismatches, and duplicate records.
The goal of Data Quality Validator is to make it easy for data teams to maintain high standards of data integrity across projects.

# Features
- Upload and validate Excel files.
- Currency validation using Language Learning Models (LLMs).
- Predefined validaton rules for missing values, data type mismatches, duplicates, range and threshold violarions 
- Download processed files easily.
- Session management and secure file handling.

# Installation Instructions
## 1. Prerequisites
- Python 3.8+
- pip package manager
- (Optional) Virtual environment tool like `venv` or `virtualenv`
- Required libraries: Flask, Openpyxl, Pandas, scikit-learn, OpenAI API, etc.

## 2. Environment Variables
If you're using OpenAI's API for currency validation, you'll need to set up an API key. 
```bash
OPENAI_API_KEY=your_api_key_here
FLASK_SECRET_KEY=your_api_key_here
```

Create a `.env` file in the root directory of the project and add:


## Steps
### 1. Clone the Repository:
git clone https://github.com/mehmet-kavrut/case_study_flask.git
cd case_study_flask

### 2. Set Up Virtual Environment (Optional but Recommended):
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Troubleshooting
- If you encounter issues with the `flask run` command, ensure you have activated the virtual environment first.
- If `pip install` fails, try upgrading `pip` using `pip install --upgrade pip`.

### 4. Run the Application
```bash
flask run
```

### 5 Access the App
Open your browser and navigate to http://127.0.0.1:5000/.

# Usage Instruction
## Web Interface:
### 1. Upload a dataset file (Excel)
### 2. View and download flagged values.

# Technologies Used
- Flask: Web Application Framework
- HTML/CSS: Used for rendering the web interface
- Openpyxl: A Python library to read/write Excel 2010 .xlsx, .xlsm, .xltx, and .xltm files.
- OpenAI API: Used for currency validation with Language Learning Models (LLMs). 
- Pandas: Python library for data processing and transformation
- Scikit-learn: Python library for machine learning-based outlier detection.
- Werkzeug: Ensures uploaded file names are sanitized.

# License
This project is licensed under the MIT License.
See the LICENSE file for more details.

# Contact Information
Maintainer: Mehmet Kavrut
Email: mehmetkavrut@gmail.com
GitHub: mehmet-kavrut
