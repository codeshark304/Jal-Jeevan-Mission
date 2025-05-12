import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import io
import json
import numpy as np
from datetime import datetime

def convert_numpy_to_native(obj):
    """
    Recursively converts NumPy data types and date objects to native Python types for JSON serialization
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: convert_numpy_to_native(v) for k, v in obj.items()}
    elif isinstance(obj, list) or isinstance(obj, tuple):
        return [convert_numpy_to_native(i) for i in obj]
    elif hasattr(obj, 'isoformat'):  # Handle date, datetime, and other objects with isoformat method
        return obj.isoformat()
    else:
        return obj

def format_percentage(val):
    """Format a value as a percentage"""
    return f"{val:.2f}%" if pd.notnull(val) else "N/A"

def format_large_number(val):
    """Format large numbers with commas for readability"""
    return f"{int(val):,}" if pd.notnull(val) else "N/A"

def create_state_progress_bar(data, title="State-wise Progress"):
    """Create a horizontal bar chart for state-wise progress"""
    # Convert data to pandas DataFrame if it's not already
    if not isinstance(data, pd.DataFrame):
        if len(data) > 0:
            # Create a pandas DataFrame from the data
            df = pd.DataFrame([
                {
                    'state_name': row.state_name,
                    'households_with_tap_water_current_pct': row.households_with_tap_water_current_pct
                }
                for row in data
            ])
        else:
            # Create an empty DataFrame with the right columns
            df = pd.DataFrame(columns=['state_name', 'households_with_tap_water_current_pct'])
    else:
        df = data
    
    if df.empty:
        # Return empty chart data if no data is available
        return {
            'data': [],
            'layout': {
                'title': title,
                'xaxis': {'title': 'Coverage (%)'},
                'yaxis': {'title': 'State/UT'},
                'annotations': [{
                    'x': 0.5,
                    'y': 0.5,
                    'xref': 'paper',
                    'yref': 'paper',
                    'text': 'No state data available',
                    'showarrow': False,
                    'font': {'size': 16}
                }]
            }
        }
    
    # Sort by percentage in descending order
    df = df.sort_values('households_with_tap_water_current_pct', ascending=False)
    
    # Create the bar chart
    fig = px.bar(
        df, 
        y='state_name', 
        x='households_with_tap_water_current_pct',
        orientation='h',
        labels={
            'state_name': 'State/UT',
            'households_with_tap_water_current_pct': 'Coverage (%)'
        },
        title=title,
        color='households_with_tap_water_current_pct',
        color_continuous_scale='viridis',
        range_color=[0, 100]
    )
    
    # Update layout
    fig.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=40, b=0),
        coloraxis_colorbar=dict(title="Coverage %"),
        xaxis_title="Coverage (%)",
        yaxis_title="",
        yaxis=dict(autorange="reversed")  # Reverse y-axis to have highest values at the top
    )
    
    # Format hover text
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Coverage: %{x:.2f}%<extra></extra>"
    )
    
    # Convert to JSON-serializable format
    return fig.to_dict()

def create_pie_chart(data, title="Distribution"):
    """Create a pie chart"""
    # Convert data to pandas DataFrame if it's not already
    if not isinstance(data, pd.DataFrame):
        if not data:  # Empty data
            # Create a placeholder dataframe
            df = pd.DataFrame(columns=['name', 'value'])
        elif len(data) > 0 and len(data[0]) == 2:  # If data has 2 columns (name, value)
            df = pd.DataFrame(data, columns=['name', 'value'])
        elif len(data) > 0:  # If data has 3 columns (name, value, percentage)
            df = pd.DataFrame(data, columns=['name', 'value', 'percentage'])
        else:
            df = pd.DataFrame(columns=['name', 'value'])
    else:
        df = data
    
    # Create the pie chart
    fig = px.pie(
        df,
        names='name',
        values='value',
        title=title
    )
    
    # Update layout
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    # Update trace for better hover info
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Value: %{value:,}<br>Percentage: %{percent}<extra></extra>"
    )
    
    # Convert to JSON-serializable format
    return fig.to_dict()

def create_gauge_chart(value, title="Progress", max_value=100):
    """Create a gauge chart for overall progress"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        title={'text': title},
        domain={'x': [0, 1], 'y': [0, 1]},
        gauge={
            'axis': {'range': [0, max_value]},
            'bar': {'color': "#1f77b4"},
            'steps': [
                {'range': [0, max_value/3], 'color': "#f7dc6f"},
                {'range': [max_value/3, 2*max_value/3], 'color': "#7fb3d5"},
                {'range': [2*max_value/3, max_value], 'color': "#82e0aa"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': value
            }
        }
    ))
    
    fig.update_layout(
        height=250,
        margin=dict(l=20, r=20, t=50, b=20)
    )
    
    # Convert to JSON-serializable format
    return fig.to_dict()

def create_time_series(data, title="Historical Progress"):
    """Create a time series line chart"""
    # Convert data to pandas DataFrame if it's not already
    if not isinstance(data, pd.DataFrame):
        if len(data) > 0:
            # Create a pandas DataFrame with the historical data
            df = pd.DataFrame([
                {
                    'state_name': entry.state_name,
                    'year': entry.year,
                    'households_with_tap_water': entry.households_with_tap_water,
                    'households_with_tap_water_pct': entry.households_with_tap_water_pct
                }
                for entry in data
            ])
        else:
            # Create an empty DataFrame with the right columns
            df = pd.DataFrame(columns=['state_name', 'year', 'households_with_tap_water', 'households_with_tap_water_pct'])
    else:
        df = data
    
    if df.empty:
        # Return empty chart data if no data is available
        return {
            'data': [],
            'layout': {
                'title': title,
                'xaxis': {'title': 'Year'},
                'yaxis': {'title': 'Coverage (%)'},
                'annotations': [{
                    'x': 0.5,
                    'y': 0.5,
                    'xref': 'paper',
                    'yref': 'paper',
                    'text': 'No historical data available',
                    'showarrow': False,
                    'font': {'size': 16}
                }]
            }
        }
    
    # Create the line chart
    fig = px.line(
        df,
        x='year',
        y='households_with_tap_water_pct',
        color='state_name',
        title=title,
        labels={
            'year': 'Year',
            'households_with_tap_water_pct': 'Coverage (%)',
            'state_name': 'State/UT'
        }
    )
    
    # Update layout
    fig.update_layout(
        height=400,
        margin=dict(l=0, r=0, t=40, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(tickformat="%Y")
    )
    
    # Format hover text
    fig.update_traces(
        hovertemplate="<b>%{customdata}</b><br>Date: %{x|%Y-%m-%d}<br>Coverage: %{y:.2f}%<extra></extra>",
        customdata=[state for state in df['state_name']]
    )
    
    # Convert to JSON-serializable format
    return fig.to_dict()

def export_to_csv(data):
    """Export data to CSV"""
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data
    
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

def export_to_excel(data):
    """Export data to Excel"""
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data
    
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_buffer.seek(0)
    return excel_buffer.getvalue()

def generate_report_text(data, title="Jal Jeevan Mission Report"):
    """Generate a text report based on the data"""
    if not isinstance(data, pd.DataFrame):
        df = pd.DataFrame(data)
    else:
        df = data
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report = [
        f"# {title}",
        f"Generated on: {now}\n",
        "## Summary"
    ]
    
    # Add summary statistics if available
    if 'total_rural_households' in df.columns and 'households_with_tap_water_current' in df.columns:
        total_households = df['total_rural_households'].sum()
        households_with_tap = df['households_with_tap_water_current'].sum()
        coverage = (households_with_tap / total_households) * 100 if total_households > 0 else 0
        
        report.extend([
            f"Total Rural Households: {format_large_number(total_households)}",
            f"Households with Tap Water: {format_large_number(households_with_tap)}",
            f"Overall Coverage: {format_percentage(coverage)}\n"
        ])
    
    # Add table header
    report.append("## Detailed Data\n")
    report.append("| " + " | ".join(df.columns) + " |")
    report.append("| " + " | ".join(["---" for _ in df.columns]) + " |")
    
    # Add table rows
    for _, row in df.iterrows():
        formatted_row = []
        for val in row:
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if val % 1 == 0:  # Integer
                    formatted_row.append(format_large_number(val))
                else:  # Float/percentage
                    formatted_row.append(format_percentage(val))
            else:
                formatted_row.append(str(val))
        
        report.append("| " + " | ".join(formatted_row) + " |")
    
    return "\n".join(report)