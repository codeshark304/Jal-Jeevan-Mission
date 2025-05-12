from flask import Blueprint, render_template, Response, send_file, flash
from flask_login import login_required
import io
from database import get_comprehensive_data
from utils import export_to_csv, export_to_excel, generate_report_text

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/')
@login_required
def index():
    return render_template('reports/index.html')

@reports_bp.route('/export/csv')
@login_required
def export_csv():
    # Get data and export to CSV
    data = get_comprehensive_data()
    csv_data = export_to_csv(data)
    
    # Create a file-like buffer to receive the CSV data
    buffer = io.BytesIO()
    buffer.write(csv_data.encode())
    buffer.seek(0)
    
    # Return the CSV file as a download
    return Response(
        buffer,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=jal_jeevan_mission_data.csv"}
    )

@reports_bp.route('/export/excel')
@login_required
def export_excel():
    # Get data and export to Excel
    data = get_comprehensive_data()
    excel_file = export_to_excel(data)
    
    # Return the Excel file as a download
    return send_file(
        excel_file,
        as_attachment=True,
        download_name="jal_jeevan_mission_data.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@reports_bp.route('/generate/text')
@login_required
def generate_text():
    # Get data and generate text report
    data = get_comprehensive_data()
    report_text = generate_report_text(data)
    
    # Create a file-like buffer to receive the text report
    buffer = io.BytesIO()
    buffer.write(report_text.encode())
    buffer.seek(0)
    
    # Return the text report as a download
    return Response(
        buffer,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment;filename=jal_jeevan_mission_report.txt"}
    )