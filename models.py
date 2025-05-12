from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, Float, String, ForeignKey, Text, Date, CheckConstraint

db = SQLAlchemy()

class StatesUTs(db.Model):
    __tablename__ = "States_UTs"
    
    state_id = Column(Integer, primary_key=True, autoincrement=True)
    state_name = Column(String(255), unique=True, nullable=False)
    
    # Relationships
    household_stats = relationship("HouseholdStats", back_populates="state", uselist=False)
    water_connections = relationship("WaterConnections", back_populates="state", uselist=False)
    historical_progress = relationship("HistoricalProgress", back_populates="state")
    
    def __repr__(self):
        return f"<State {self.state_name}>"

class HouseholdStats(db.Model):
    __tablename__ = "Household_Stats"
    
    state_id = Column(Integer, ForeignKey("States_UTs.state_id", ondelete="CASCADE"), primary_key=True)
    total_rural_households = Column(Integer, nullable=False)
    households_with_tap_water_current = Column(Integer, nullable=False)
    households_with_tap_water_current_pct = Column(Float, nullable=False)
    
    # Relationships
    state = relationship("StatesUTs", back_populates="household_stats")
    
    def __repr__(self):
        return f"<HouseholdStats for {self.state.state_name if self.state else 'Unknown'}: {self.households_with_tap_water_current_pct}%>"

class WaterConnections(db.Model):
    __tablename__ = "Water_Connections"
    
    state_id = Column(Integer, ForeignKey("States_UTs.state_id", ondelete="CASCADE"), primary_key=True)
    tap_water_connections_provided = Column(Integer, nullable=False)
    tap_water_connections_provided_pct = Column(Float, nullable=False)
    
    # Relationships
    state = relationship("StatesUTs", back_populates="water_connections")
    
    def __repr__(self):
        return f"<WaterConnections for {self.state.state_name if self.state else 'Unknown'}: {self.tap_water_connections_provided} connections>"

class HistoricalProgress(db.Model):
    __tablename__ = "Historical_Progress"
    
    state_id = Column(Integer, ForeignKey("States_UTs.state_id", ondelete="CASCADE"), primary_key=True)
    year = Column(Date, primary_key=True)
    households_with_tap_water = Column(Integer, nullable=False)
    households_with_tap_water_pct = Column(Float, nullable=False)
    
    # Relationships
    state = relationship("StatesUTs", back_populates="historical_progress")
    
    def __repr__(self):
        return f"<HistoricalProgress for {self.state.state_name if self.state else 'Unknown'} on {self.year}: {self.households_with_tap_water_pct}%>"

class User(db.Model):
    __tablename__ = "Users"
    
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False)
    
    
    # Ensure role is either 'admin' or 'viewer'
    __table_args__ = (
        CheckConstraint("role IN ('admin', 'viewer')", name='check_role'),
    )
    
    def __repr__(self):
        return f"<User {self.username} ({self.role})>"