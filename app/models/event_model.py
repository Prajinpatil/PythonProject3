"""
Event Model - Database schema for events
"""

from sqlalchemy import Column, String, Float, DateTime, JSON, Integer, Text
from sqlalchemy.sql import func
from datetime import datetime

from app.database.db import Base


class Event(Base):
    """
    Event table - stores all intrusion detection events
    """
    __tablename__ = "events"
    
    # Primary key
    event_id = Column(String(50), primary_key=True, index=True)
    
    # Source information
    camera_id = Column(String(50), nullable=False, index=True)
    zone_id = Column(String(50), nullable=False, index=True)
    
    # Detection data
    object_type = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    # Threat assessment
    threat_score = Column(Float, nullable=False, index=True)
    threat_level = Column(String(20), nullable=False, index=True)
    
    # Status
    status = Column(String(20), default="NEW", nullable=False, index=True)
    
    # Timestamps
    detected_at = Column(DateTime, nullable=False, index=True, default=func.now())
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    
    # Media URLs
    image_url = Column(String(500))
    video_url = Column(String(500))
    
    # Additional data
    metadata = Column(JSON, default=dict)
    notes = Column(Text)
    operator_id = Column(String(50))
    
    def __repr__(self):
        return f"<Event {self.event_id}: {self.object_type} in {self.zone_id} (Threat: {self.threat_level})>"
    
    def to_dict(self):
        """Convert to dictionary for API response"""
        return {
            "event_id": self.event_id,
            "camera_id": self.camera_id,
            "zone_id": self.zone_id,
            "object_type": self.object_type,
            "confidence": self.confidence,
            "threat_score": self.threat_score,
            "threat_level": self.threat_level,
            "status": self.status,
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "image_url": self.image_url,
            "video_url": self.video_url,
            "metadata": self.metadata or {},
            "notes": self.notes,
            "operator_id": self.operator_id
        }


class Alert(Base):
    """
    Alert table - stores triggered alerts
    """
    __tablename__ = "alerts"
    
    # Primary key
    alert_id = Column(String(50), primary_key=True, index=True)
    
    # Related event
    event_id = Column(String(50), nullable=False, index=True)
    
    # Alert data
    priority = Column(String(20), nullable=False, index=True)
    status = Column(String(20), default="ACTIVE", nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=func.now())
    acknowledged_at = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Handling
    acknowledged_by = Column(String(50))
    notes = Column(Text)
    
    # Additional data
    metadata = Column(JSON, default=dict)
    
    def __repr__(self):
        return f"<Alert {self.alert_id}: {self.priority} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "event_id": self.event_id,
            "priority": self.priority,
            "status": self.status,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "acknowledged_by": self.acknowledged_by,
            "notes": self.notes,
            "metadata": self.metadata or {}
        }
