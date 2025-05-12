from flask import Blueprint, render_template, flash
from flask_login import login_required
import json
from database import get_historical_progress
from utils import create_time_series

historical_progress_bp = Blueprint('historical_progress', __name__)

@historical_progress_bp.route('/')
@login_required
def index():
    try:
        # Get historical progress data
        progress_data = get_historical_progress()
        
        # Create time series chart
        time_series_data = create_time_series(progress_data, title="Historical Progress by State")
        
        return render_template(
            'historical_progress/index.html',
            progress_data=progress_data,
            time_series_data=json.dumps(time_series_data)
        )
    except Exception as e:
        flash(f"Error loading historical progress: {str(e)}", "danger")
        return render_template(
            'historical_progress/index.html',
            progress_data=[],
            time_series_data="{}"
        )
    
# Not required