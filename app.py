import os
from flask import Flask, render_template, request, send_file, session, redirect, url_for, flash
import uuid
from werkzeug.utils import secure_filename
from validators import CurrencyCheckerLLM, ExcelValidator
import pandas as pd
import time

app = Flask(__name__)
app.secret_key = 'supersecretkey'

UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'xlsx'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)

        # Session specific ID
        session_id = str(int(time.time()))
        output_excel_path = os.path.join(OUTPUT_FOLDER, f"{session_id}_validated.xlsx")
        output_csv_path = os.path.join(OUTPUT_FOLDER, f"{session_id}_flagged.csv")

        file.save(input_path)

        try:
            validator = ExcelValidator(input_path)
            validated_df = validator.validate_all()

            checker = CurrencyCheckerLLM(batch_size=5, max_retries=3, retry_delay=5)
            df_checked = checker.check_currency(validated_df)

            # Save full validated file
            df_checked.to_excel(output_excel_path, index=False)

            # Save only flagged rows (for showing in UI)
            flagged_df = df_checked[
                (df_checked['companynameofficial_inconsistent']) |
                (df_checked['geonameen_inconsistent']) |
                (df_checked['revenue_outlier']) |
                (df_checked['dbscan_outlier_flag']) |
                (df_checked['IQR_outlier_flag']) |
                (df_checked['negative_revenue_flag']) |
                (df_checked['currency_check_flag'])
            ]


            flagged_df.to_csv(output_csv_path, index=False)

            return redirect(url_for('show_results', session_id=session_id))

        except Exception as e:
            flash(f"Error processing file: {e}")
            return redirect(url_for('index'))

    flash('Invalid file type. Only .xlsx allowed.')
    return redirect(url_for('index'))


@app.route('/results/<session_id>')
def show_results(session_id):
    temp_path = os.path.join(OUTPUT_FOLDER, f"{session_id}_flagged.csv")
    if not os.path.exists(temp_path):
        flash('No flagged data found.')
        return redirect(url_for('index'))
    
    flagged_df = pd.read_csv(temp_path)

    flag_columns = [
        'companynameofficial_inconsistent', 'geonameen_inconsistent',
        'revenue_outlier', 'dbscan_outlier_flag', 'IQR_outlier_flag', 
        'negative_revenue_flag', 'currency_check_flag'
    ]

    def highlight_true(val):
        if val is True or str(val).lower() == 'true':
            return 'background-color: #ffcccc'
        return ''
    
    styled_df = (
        flagged_df.style
        .applymap(highlight_true, subset=flag_columns)
    )

    table_html = styled_df.to_html()

    return render_template('results.html', table_html=table_html, session_id=session_id)


@app.route('/download/<session_id>')
def download_flagged(session_id):
    output_excel_path = os.path.join(OUTPUT_FOLDER, f"{session_id}_validated.xlsx")
    if not os.path.exists(output_excel_path):
        flash('Validated file not found.')
        return redirect(url_for('index'))

    return send_file(output_excel_path, as_attachment=True)



if __name__ == '__main__':
    app.run(debug=True)
