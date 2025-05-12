from flask import Blueprint, render_template, flash
from flask_login import login_required
import json
from database import get_overall_statistics, get_comprehensive_data, get_top_states, get_bottom_states
from utils import create_gauge_chart, create_state_progress_bar, create_pie_chart, convert_numpy_to_native
import plotly
import pandas as pd

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
@login_required
def index():
    try:
        # Get data from database
        stats = get_overall_statistics()
        comprehensive_data = get_comprehensive_data() or []
        top_states = get_top_states(count=5, by_coverage=True) or []
        bottom_states = get_bottom_states(count=5) or []
        
        # Create gauge chart for overall progress
        gauge_data = create_gauge_chart(
            value=stats.get('coverage_percentage', 0), 
            title="Overall Coverage", 
            max_value=100
        )
        
        # Create state progress bar chart
        if comprehensive_data:
            state_progress_data = create_state_progress_bar(
                comprehensive_data, 
                title="State-wise Progress"
            )
        else:
            # Create empty bar chart
            state_progress_data = create_state_progress_bar(
                pd.DataFrame(columns=['state_name', 'households_with_tap_water_current_pct']),
                title="State-wise Progress (No Data)"
            )
        
        # Create top states pie chart
        top_states_data = create_pie_chart(
            [(state[0], state[2]) for state in top_states] if top_states else [], 
            title="Top 5 States by Coverage (%)"
        )
        
        # Create bottom states pie chart
        bottom_states_data = create_pie_chart(
            [(state[0], state[2]) for state in bottom_states] if bottom_states else [], 
            title="States Needing Attention (%)"
        )
        
        # If we have no data, show a message
        if not comprehensive_data:
            flash("No data available. Please add data using the Data Management section.", "info")
        
        try:
            # Debug print statements
            print("DEBUG: Converting gauge data")
            gauge_json = json.dumps(convert_numpy_to_native(gauge_data), cls=plotly.utils.PlotlyJSONEncoder)
            
            print("DEBUG: Converting state progress data")
            state_progress_json = json.dumps(convert_numpy_to_native(state_progress_data), cls=plotly.utils.PlotlyJSONEncoder)
            
            print("DEBUG: Converting top states data")
            top_states_json = json.dumps(convert_numpy_to_native(top_states_data), cls=plotly.utils.PlotlyJSONEncoder)
            
            print("DEBUG: Converting bottom states data")
            bottom_states_json = json.dumps(convert_numpy_to_native(bottom_states_data), cls=plotly.utils.PlotlyJSONEncoder)
            
            return render_template(
                'dashboard/index.html',
                stats=stats,
                comprehensive_data=comprehensive_data,
                gauge_data=gauge_json if gauge_json else "{}",
                state_progress_data=state_progress_json if state_progress_json else "{}",
                top_states_data=top_states_json if top_states_json else "{}",
                bottom_states_data=bottom_states_json if bottom_states_json else "{}"
            )
        except Exception as e:
            print(f"DEBUG JSON ERROR: {str(e)}")
            # Fallback to safe empty JSON objects if JSON serialization fails
            return render_template(
                'dashboard/index.html',
                stats=stats,
                comprehensive_data=comprehensive_data,
                gauge_data="{}",
                state_progress_data="{}",
                top_states_data="{}",
                bottom_states_data="{}"
            )
            
    except Exception as e:
        flash(f"Error loading dashboard: {str(e)}", "danger")
        return render_template(
            'dashboard/index.html',
            stats={"total_households": 0, "households_with_tap": 0, "coverage_percentage": 0, "connections_provided": 0},
            comprehensive_data=[],
            gauge_data="{}",
            state_progress_data="{}",
            top_states_data="{}",
            bottom_states_data="{}"
        )