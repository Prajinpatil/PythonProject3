"""
Alert Schemas - Real-time Notifications
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

from app.schemas.event_schema import ThreatLevel, ObjectType


class AlertPriority(str, Enum):
    """Alert priority levels"""
    critical = "CRITICAL"
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"


class AlertStatus(str, Enum):
    """Alert lifecycle"""
    active = "ACTIVE"
    acknowledged = "ACKNOWLEDGED"
    resolved = "RESOLVED"
    dismissed = "DISMISSED"


class AlertCreate(BaseModel):
    """Create new alert from event"""
    event_id: str
    priority: AlertPriority
    message: str = Field(..., max_length=500)
    metadata: Optional[dict] = Field(default_factory=dict)


class AlertResponse(BaseModel):
    """Alert data returned to frontend"""
    alert_id: str
    event_id: str
    priority: AlertPriority
    status: AlertStatus
    message: str
    
    # Event context
    camera_id: str
    zone_id: str
    zone_name: Optional[str] = None
    object_type: ObjectType
    threat_level: ThreatLevel
    threat_score: float
    
    # Timestamps
    created_at: datetime
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Handling
    acknowledged_by: Optional[str] = None
    notes: Optional[str] = None
    metadata: dict = Field(default_factory=dict)
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "alert_id": "ALT_20240207_001",
                "event_id": "EVT_20240207_001",
                "priority": "CRITICAL",
                "status": "ACTIVE",
                "message": "Critical threat detected: Human in restricted zone during night",
                "camera_id": "CAM003",
                "zone_id": "Z003",
                "zone_name": "Server Room",
                "object_type": "human",
                "threat_level": "critical",
                "threat_score": 88.5,
                "created_at": "2024-02-07T22:30:00Z"
            }
        }


class AlertUpdate(BaseModel):
    """Update alert status"""
    status: AlertStatus
    notes: Optional[str] = Field(None, max_length=500)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "ACKNOWLEDGED",
                "notes": "Security team dispatched"
            }
        }


class AlertListResponse(BaseModel):
    """List of alerts"""
    alerts: List[AlertResponse]
    total: int
    active_count: int
    critical_count: int


class AlertStats(BaseModel):
    """Alert statistics"""
    total_alerts: int
    active_alerts: int
    critical_alerts: int
    high_alerts: int
    
    # Response times
    avg_acknowledgement_seconds: Optional[float] = None
    avg_resolution_seconds: Optional[float] = None
    
    # By zone
    alerts_by_zone: List[dict] = Field(default_factory=list)
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_alerts": 156,
                "active_alerts": 12,
                "critical_alerts": 5,
                "high_alerts": 7,
                "avg_acknowledgement_seconds": 45.2,
                "avg_resolution_seconds": 320.5,
                "alerts_by_zone": [
                    {"zone_id": "Z003", "zone_name": "Server Room", "count": 34},
                    {"zone_id": "Z001", "zone_name": "Main Entrance", "count": 28}
                ]
            }
        }
