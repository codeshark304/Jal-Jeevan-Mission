import os
import pandas as pd
from models import db, User, StatesUTs, HouseholdStats, WaterConnections, HistoricalProgress
from sqlalchemy import text
import time
import hashlib
from auth import hash_password

def get_connection_string():
    """Get database connection string from environment variables"""
    # First try to use PostgreSQL (for production)
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        # Fix heroku style postgres:// URLs
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        return database_url
    
    # If PostgreSQL environment variables are available, construct the connection string
    pg_host = os.environ.get('PGHOST')
    pg_port = os.environ.get('PGPORT')
    pg_user = os.environ.get('PGUSER')
    pg_pass = os.environ.get('PGPASSWORD')
    pg_db = os.environ.get('PGDATABASE')
    
    if all([pg_host, pg_port, pg_user, pg_pass, pg_db]):
        return f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
    
    # Fallback to SQLite for development
    return 'sqlite:///jal_jeevan_mission.db'

def init_db(app):
    """Initialize database, create tables and default admin user"""
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Add default admin user if it doesn't exist
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=hash_password('admin123'),
                role='admin'
            )
            
            try:
                db.session.add(admin_user)
                db.session.commit()
                print("Created default admin user.")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating default admin: {str(e)}")
        
        # Optional: Add test user for development
        if not User.query.filter_by(username='monish').first():
            test_user = User(
                username='monish',
                password_hash=hash_password('DBSP312'),
                role='admin'
            )
            
            try:
                db.session.add(test_user)
                db.session.commit()
                print("Created test user.")
            except Exception as e:
                db.session.rollback()
                print(f"Error creating test user: {str(e)}")

def retry_db_operation(func, max_retries=3):
    """Retry a database operation with exponential backoff"""
    retries = 0
    while retries < max_retries:
        try:
            return func()
        except Exception as e:
            retries += 1
            if retries >= max_retries:
                raise e
            
            # Exponential backoff
            wait_time = 0.5 * (2 ** retries)
            print(f"Database operation failed. Retrying in {wait_time:.2f} seconds... ({retries}/{max_retries})")
            time.sleep(wait_time)

def get_states():
    """Get all states and union territories"""
    def query_func():
        return StatesUTs.query.order_by(StatesUTs.state_name).all()
    
    return retry_db_operation(query_func)

def get_household_stats():
    """Get household statistics with state names"""
    def query_func():
        return db.session.query(
            StatesUTs.state_name,
            HouseholdStats.total_rural_households,
            HouseholdStats.households_with_tap_water_current,
            HouseholdStats.households_with_tap_water_current_pct
        ).join(
            HouseholdStats, 
            StatesUTs.state_id == HouseholdStats.state_id
        ).order_by(
            StatesUTs.state_name
        ).all()
    
    return retry_db_operation(query_func)

def get_water_connections():
    """Get water connection data with state names"""
    def query_func():
        return db.session.query(
            StatesUTs.state_name,
            WaterConnections.tap_water_connections_provided,
            WaterConnections.tap_water_connections_provided_pct
        ).join(
            WaterConnections, 
            StatesUTs.state_id == WaterConnections.state_id
        ).order_by(
            StatesUTs.state_name
        ).all()
    
    return retry_db_operation(query_func)

def get_historical_progress():
    """Get historical progress data with state names"""
    def query_func():
        return db.session.query(
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
    
    return retry_db_operation(query_func)

def get_comprehensive_data():
    """Get combined data from all tables for comprehensive analysis"""
    def query_func():
        return db.session.query(
            StatesUTs,
            HouseholdStats,
            WaterConnections
        ).join(
            HouseholdStats, 
            StatesUTs.state_id == HouseholdStats.state_id,
            isouter=True
        ).join(
            WaterConnections, 
            StatesUTs.state_id == WaterConnections.state_id,
            isouter=True
        ).order_by(
            StatesUTs.state_name
        ).all()
    
    return retry_db_operation(query_func)

def get_overall_statistics():
    """Get overall mission statistics"""
    def query_func():
        stats = {}
        
        # Get total households and coverage
        household_query = db.session.query(
            db.func.sum(HouseholdStats.total_rural_households).label('total_households'),
            db.func.sum(HouseholdStats.households_with_tap_water_current).label('households_with_tap')
        ).first()
        
        if household_query and household_query.total_households:
            stats['total_households'] = household_query.total_households
            stats['households_with_tap'] = household_query.households_with_tap
            stats['coverage_percentage'] = (household_query.households_with_tap / household_query.total_households) * 100
        else:
            stats['total_households'] = 0
            stats['households_with_tap'] = 0
            stats['coverage_percentage'] = 0
        
        # Get total connections provided
        connection_query = db.session.query(
            db.func.sum(WaterConnections.tap_water_connections_provided).label('connections_provided')
        ).first()
        
        if connection_query:
            stats['connections_provided'] = connection_query.connections_provided or 0
        else:
            stats['connections_provided'] = 0
        
        return stats
    
    return retry_db_operation(query_func)

def get_top_states(count=5, by_coverage=True):
    """Get top performing states by coverage percentage or absolute numbers"""
    def query_func():
        if by_coverage:
            # Get top states by coverage percentage
            return db.session.query(
                StatesUTs.state_name,
                HouseholdStats.households_with_tap_water_current,
                HouseholdStats.households_with_tap_water_current_pct
            ).join(
                HouseholdStats, 
                StatesUTs.state_id == HouseholdStats.state_id
            ).order_by(
                HouseholdStats.households_with_tap_water_current_pct.desc()
            ).limit(count).all()
        else:
            # Get top states by absolute number of connections
            return db.session.query(
                StatesUTs.state_name,
                HouseholdStats.households_with_tap_water_current,
                HouseholdStats.households_with_tap_water_current_pct
            ).join(
                HouseholdStats, 
                StatesUTs.state_id == HouseholdStats.state_id
            ).order_by(
                HouseholdStats.households_with_tap_water_current.desc()
            ).limit(count).all()
    
    return retry_db_operation(query_func)

def get_bottom_states(count=5):
    """Get states needing attention (bottom performers by coverage percentage)"""
    def query_func():
        return db.session.query(
            StatesUTs.state_name,
            HouseholdStats.households_with_tap_water_current,
            HouseholdStats.households_with_tap_water_current_pct
        ).join(
            HouseholdStats, 
            StatesUTs.state_id == HouseholdStats.state_id
        ).filter(
            HouseholdStats.households_with_tap_water_current_pct < 100  # Exclude states with 100% coverage
        ).order_by(
            HouseholdStats.households_with_tap_water_current_pct.asc()
        ).limit(count).all()
    
    return retry_db_operation(query_func)