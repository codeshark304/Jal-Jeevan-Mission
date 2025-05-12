from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, FloatField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from models import db, StatesUTs, HouseholdStats, WaterConnections, HistoricalProgress
from database import get_states, get_historical_progress
from datetime import date
from decimal import Decimal
import json
from sqlalchemy.exc import IntegrityError

data_management_bp = Blueprint('data_management', __name__)

def get_historical_progress_data():
    """Helper function to get historical progress data with state names"""
    try:
        def get_progress():
            return db.session.query(
                StatesUTs.state_id,
                StatesUTs.state_name,
                HistoricalProgress.year,
                HistoricalProgress.households_with_tap_water,
                HistoricalProgress.households_with_tap_water_pct
            ).join(
                HistoricalProgress, 
                StatesUTs.state_id == HistoricalProgress.state_id
            ).order_by(
                StatesUTs.state_name,
                HistoricalProgress.year
            ).all()
        
        return get_progress()
    except Exception as e:
        flash(f"Error retrieving historical progress data: {str(e)}", "danger")
        return []

# Forms
class StateForm(FlaskForm):
    state_name = StringField('State/UT Name', validators=[DataRequired()])
    submit = SubmitField('Save State')

class HouseholdStatsForm(FlaskForm):
    state_id = SelectField('State/UT', validators=[DataRequired()], coerce=int)
    total_rural_households = IntegerField('Total Rural Households', 
                                        validators=[DataRequired(), NumberRange(min=1)])
    households_with_tap_water_current = IntegerField('Households with Tap Water', 
                                                   validators=[DataRequired(), NumberRange(min=0)])
    calculate_percentage = SubmitField('Calculate Percentage')
    households_with_tap_water_current_pct = FloatField('Coverage Percentage (%)', 
                                                      validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Household Stats')

class WaterConnectionsForm(FlaskForm):
    state_id = SelectField('State/UT', validators=[DataRequired()], coerce=int)
    tap_water_connections_provided = IntegerField('Tap Water Connections Provided', 
                                                validators=[DataRequired(), NumberRange(min=0)])
    tap_water_connections_provided_pct = FloatField('Percentage (%)', 
                                                  validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Water Connections')

class HistoricalProgressForm(FlaskForm):
    state_id = SelectField('State/UT', validators=[DataRequired()], coerce=int)
    year = DateField('Date', validators=[DataRequired()], default=date.today)
    households_with_tap_water = IntegerField('Households with Tap Water', 
                                           validators=[DataRequired(), NumberRange(min=0)])
    calculate_percentage = SubmitField('Calculate Percentage')
    households_with_tap_water_pct = FloatField('Coverage Percentage (%)', 
                                             validators=[DataRequired(), NumberRange(min=0, max=100)])
    submit = SubmitField('Save Historical Progress')

@data_management_bp.route('/')
@login_required
def index():
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to access the data management section.", "danger")
        return redirect(url_for('dashboard.index'))
    
    return render_template('data_management/index.html')

@data_management_bp.route('/states', methods=['GET', 'POST'])
@login_required
def manage_states():
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('dashboard.index'))
    
    form = StateForm()
    if form.validate_on_submit():
        # Create new state
        state = StatesUTs(state_name=form.state_name.data)
        
        try:
            db.session.add(state)
            db.session.commit()
            flash(f"State/UT '{form.state_name.data}' added successfully.", "success")
            return redirect(url_for('data_management.manage_states'))
        except IntegrityError:
            db.session.rollback()
            flash(f"State/UT '{form.state_name.data}' already exists.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding state: {str(e)}", "danger")
    
    # Get all states
    states = get_states()
    
    return render_template('data_management/states.html', form=form, states=states)

@data_management_bp.route('/states/delete/<int:state_id>', methods=['POST'])
@login_required
def delete_state(state_id):
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to perform this action.", "danger")
        return redirect(url_for('dashboard.index'))
    
    state = StatesUTs.query.get_or_404(state_id)
    
    try:
        db.session.delete(state)
        db.session.commit()
        flash(f"State/UT '{state.state_name}' deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting state: {str(e)}", "danger")
    
    return redirect(url_for('data_management.manage_states'))

@data_management_bp.route('/household_stats', methods=['GET', 'POST'])
@login_required
def manage_household_stats():
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('dashboard.index'))
    
    form = HouseholdStatsForm()
    
    # Get all states for the dropdown
    states = get_states()
    form.state_id.choices = [(s.state_id, s.state_name) for s in states]
    
    if request.method == 'POST':
        if 'calculate_percentage' in request.form:
            # Calculate percentage
            total = int(request.form.get('total_rural_households', 0))
            current = int(request.form.get('households_with_tap_water_current', 0))
            
            if total > 0:
                percentage = (current / total) * 100
                percentage = round(percentage, 2)
            else:
                percentage = 0
            
            # Update form with calculated percentage
            form.state_id.data = int(request.form.get('state_id'))
            form.total_rural_households.data = total
            form.households_with_tap_water_current.data = current
            form.households_with_tap_water_current_pct.data = percentage
            
            # Return the form with the calculated percentage
            return render_template(
                'data_management/household_stats.html', 
                form=form,
                stats=get_stats()
            )
        
        elif form.validate_on_submit():
            def save_household_stats():
                # Check if stats already exist for this state
                existing_stats = HouseholdStats.query.filter_by(state_id=form.state_id.data).first()
                
                if existing_stats:
                    # Update existing stats
                    existing_stats.total_rural_households = form.total_rural_households.data
                    existing_stats.households_with_tap_water_current = form.households_with_tap_water_current.data
                    existing_stats.households_with_tap_water_current_pct = form.households_with_tap_water_current_pct.data
                    db.session.commit()
                    
                    # Get state name for the flash message
                    state = StatesUTs.query.get(form.state_id.data)
                    flash(f"Household statistics for '{state.state_name}' updated successfully.", "success")
                else:
                    # Create new stats
                    stats = HouseholdStats(
                        state_id=form.state_id.data,
                        total_rural_households=form.total_rural_households.data,
                        households_with_tap_water_current=form.households_with_tap_water_current.data,
                        households_with_tap_water_current_pct=form.households_with_tap_water_current_pct.data
                    )
                    
                    db.session.add(stats)
                    db.session.commit()
                    
                    # Get state name for the flash message
                    state = StatesUTs.query.get(form.state_id.data)
                    flash(f"Household statistics for '{state.state_name}' added successfully.", "success")
            
            try:
                save_household_stats()
                return redirect(url_for('data_management.manage_household_stats'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving household statistics: {str(e)}", "danger")
    
    # Get existing stats
    def get_stats():
        return db.session.query(
            StatesUTs.state_name,
            HouseholdStats
        ).join(
            HouseholdStats,
            StatesUTs.state_id == HouseholdStats.state_id
        ).order_by(
            StatesUTs.state_name
        ).all()
    
    return render_template(
        'data_management/household_stats.html', 
        form=form,
        stats=get_stats()
    )

@data_management_bp.route('/water_connections', methods=['GET', 'POST'])
@login_required
def manage_water_connections():
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('dashboard.index'))
    
    form = WaterConnectionsForm()
    
    # Get all states for the dropdown
    states = get_states()
    form.state_id.choices = [(s.state_id, s.state_name) for s in states]
    
    if form.validate_on_submit():
        try:
            def save_water_connections():
                # Check if connections already exist for this state
                existing_connections = WaterConnections.query.filter_by(state_id=form.state_id.data).first()
                
                if existing_connections:
                    # Update existing connections
                    existing_connections.tap_water_connections_provided = form.tap_water_connections_provided.data
                    existing_connections.tap_water_connections_provided_pct = form.tap_water_connections_provided_pct.data
                    db.session.commit()
                    
                    # Get state name for the flash message
                    state = StatesUTs.query.get(form.state_id.data)
                    flash(f"Water connections for '{state.state_name}' updated successfully.", "success")
                else:
                    # Create new connections
                    connections = WaterConnections(
                        state_id=form.state_id.data,
                        tap_water_connections_provided=form.tap_water_connections_provided.data,
                        tap_water_connections_provided_pct=form.tap_water_connections_provided_pct.data
                    )
                    
                    db.session.add(connections)
                    db.session.commit()
                    
                    # Get state name for the flash message
                    state = StatesUTs.query.get(form.state_id.data)
                    flash(f"Water connections for '{state.state_name}' added successfully.", "success")
            
            save_water_connections()
            return redirect(url_for('data_management.manage_water_connections'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error saving water connections: {str(e)}", "danger")
    
    # Get existing connections
    def get_connections():
        return db.session.query(
            StatesUTs.state_name,
            WaterConnections
        ).join(
            WaterConnections,
            StatesUTs.state_id == WaterConnections.state_id
        ).order_by(
            StatesUTs.state_name
        ).all()
    
    return render_template(
        'data_management/water_connections.html', 
        form=form,
        connections=get_connections()
    )

@data_management_bp.route('/historical_progress', methods=['GET', 'POST'])
@login_required
def manage_historical_progress():
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to access this page.", "danger")
        return redirect(url_for('dashboard.index'))
    
    form = HistoricalProgressForm()
    
    # Get all states for the dropdown
    states = get_states()
    form.state_id.choices = [(s.state_id, s.state_name) for s in states]
    
    if request.method == 'POST':
        if 'calculate_percentage' in request.form:
            # Get the total households for this state
            state_id = int(request.form.get('state_id'))
            households_stats = HouseholdStats.query.filter_by(state_id=state_id).first()
            
            if households_stats:
                total = households_stats.total_rural_households
                current = int(request.form.get('households_with_tap_water', 0))
                
                if total > 0:
                    percentage = (current / total) * 100
                    percentage = round(percentage, 2)
                else:
                    percentage = 0
                
                # Update form with calculated percentage
                form.state_id.data = state_id
                form.year.data = date.fromisoformat(request.form.get('year'))
                form.households_with_tap_water.data = current
                form.households_with_tap_water_pct.data = percentage
                
                # Return the form with the calculated percentage
                return render_template(
                    'data_management/historical_progress.html', 
                    form=form,
                    progress_data=get_historical_progress_data()
                )
            else:
                flash("Could not find household statistics for this state. Please add household statistics first.", "warning")
                
        elif form.validate_on_submit():
            try:
                def save_historical_progress():
                    # Check if progress already exists for this state and year
                    existing_progress = HistoricalProgress.query.filter_by(
                        state_id=form.state_id.data,
                        year=form.year.data
                    ).first()
                    
                    if existing_progress:
                        # Update existing progress
                        existing_progress.households_with_tap_water = form.households_with_tap_water.data
                        existing_progress.households_with_tap_water_pct = form.households_with_tap_water_pct.data
                        db.session.commit()
                        
                        # Get state name for the flash message
                        state = StatesUTs.query.get(form.state_id.data)
                        flash(f"Historical progress for '{state.state_name}' on {form.year.data} updated successfully.", "success")
                    else:
                        # Create new progress
                        progress = HistoricalProgress(
                            state_id=form.state_id.data,
                            year=form.year.data,
                            households_with_tap_water=form.households_with_tap_water.data,
                            households_with_tap_water_pct=form.households_with_tap_water_pct.data
                        )
                        
                        db.session.add(progress)
                        db.session.commit()
                        
                        # Get state name for the flash message
                        state = StatesUTs.query.get(form.state_id.data)
                        flash(f"Historical progress for '{state.state_name}' on {form.year.data} added successfully.", "success")
                
                save_historical_progress()
                return redirect(url_for('data_management.manage_historical_progress'))
            except Exception as e:
                db.session.rollback()
                flash(f"Error saving historical progress: {str(e)}", "danger")
    
    return render_template(
        'data_management/historical_progress.html', 
        form=form,
        progress_data=get_historical_progress_data()
    )

@data_management_bp.route('/historical_progress/delete/<int:state_id>/<path:date>', methods=['POST'])
@login_required
def delete_historical_progress(state_id, date):
    # Check if user is admin
    if current_user.role != 'admin':
        flash("You don't have permission to perform this action.", "danger")
        return redirect(url_for('dashboard.index'))
    
    try:
        def delete_progress():
            # Parse the date from the URL-safe format
            year_date = date.replace('_', '-')
            progress_date = date.fromisoformat(year_date)
            
            # Find the progress record
            progress = HistoricalProgress.query.filter_by(
                state_id=state_id,
                year=progress_date
            ).first()
            
            if progress:
                # Get state name for the flash message
                state = StatesUTs.query.get(state_id)
                
                # Delete the progress
                db.session.delete(progress)
                db.session.commit()
                
                flash(f"Historical progress for '{state.state_name}' on {progress_date} deleted successfully.", "success")
            else:
                flash("Historical progress record not found.", "danger")
        
        delete_progress()
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting historical progress: {str(e)}", "danger")
    
    return redirect(url_for('data_management.manage_historical_progress'))