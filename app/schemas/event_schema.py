"""
Event Schemas - API Contracts for Event Data
Defines what frontend sends and backend returns
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# ========== ENUMS ==========
class ObjectType(str, Enum):
    """Detected object types"""
    human = "human"
    vehicle = "vehicle"
    animal = "animal"
    drone = "drone"
    weapon = "weapon"
    bag = "bag"
    package = "package"
    unknown = "unknown"


class EventStatus(str, Enum):
    """Event lifecycle status"""
    new = "NEW"
    investigating = "INVESTIGATING"
    resolved = "RESOLVED"
    false_positive = "FALSE_POSITIVE"
    escalated = "ESCALATED"


class ThreatLevel(str, Enum):
    """Threat severity levels"""
    critical = "critical"
    high = "high"
    medium = "medium"
    low = "low"
    minimal = "minimal"


# ========== REQUEST SCHEMAS ==========
class EventCreate(BaseModel):
    """
    Schema for creating new event
    What camera systems send to backend
    """
    camera_id: str = Field(..., description="Camera identifier", min_length=1, max_length=50)
    zone_id: str = Field(..., description="Zone identifier", min_length=1, max_length=50)
    object_type: ObjectType = Field(..., description="Type of object detected")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Detection confidence (0-1)")
    
    # Optional metadata
    image_url: Optional[str] = Field(None, description="URL to event image/snapshot")
    video_url: Optional[str] = Field(None, description="URL to event video clip")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional context")
    
    @validator('camera_id', 'zone_id')
    def validate_ids(cls, v):
        """Ensure IDs don't contain dangerous characters"""
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("IDs can only contain alphanumeric, dash, underscore")
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "camera_id": "CAM001",
                "zone_id": "Z001",
                "object_type": "human",
                "confidence": 0.94,
                "image_url": "https://storage.example.com/events/img_001.jpg",
                "metadata": {"direction": "entering", "count": 1}
            }
        }


class EventUpdate(BaseModel):
    """Schema for updating event status"""
    status: EventStatus
    notes: Optional[str] = Field(None, max_length=500)
    operator_id: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "RESOLVED",
                "notes": "False alarm - maintenance personnel",
                "operator_id": "U002"
            }
        }


# ========== RESPONSE SCHEMAS ==========
class EventResponse(BaseModel):
    """
    Complete event data returned to frontend
    Includes computed threat score
    """
    event_id: str = Field(..., description="Unique event identifier")
    camera_id: str
    zone_id: str
    zone_name: Optional[str] = None
    object_type: ObjectType
    confidence: float
    
    # Threat analysis
    threat_score: float = Field(..., description="Computed threat score (0-100)")
    threat_level: ThreatLevel = Field(..., description="Threat severity")
    
    # Status
    status: EventStatus
    
    # Timestamps
    detected_at: datetime = Field(..., description="When event was detected")
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Media
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    
    # Additional context
    metadata: dict = Field(default_factory=dict)
    notes: Optional[str] = None
    operator_id: Optional[str] = None
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "event_id": "EVT_20240207_001",
                "camera_id": "CAM001",
                "zone_id": "Z001",
                "zone_name": "Main Entrance",
                "object_type": "human",
                "confidence": 0.94,
                "threat_score": 72.5,
                "threat_level": "high",
                "status": "NEW",
                "detected_at": "2024-02-07T22:30:00Z",
                "created_at": "2024-02-07T22:30:01Z",
                "image_url": "https://storage.example.com/events/img_001.jpg",
                "metadata": {"time_period": "night"}
            }
        }


class EventListResponse(BaseModel):
    """Paginated list of events"""
    events: List[EventResponse]
    total: int
    page: int = 1
    page_size: int = 50
    has_more: bool = False


# ========== LIVE STREAM SCHEMA ==========
class LiveEventStream(BaseModel):
    """Real-time event for WebSocket streaming"""
    event: EventResponse
    alert_triggered: bool = False
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "event": {
                    "event_id": "EVT_20240207_001",
                    "threat_score": 85.0,
                    "threat_level": "critical"
                },
                "alert_triggered": True,
                "timestamp": "2024-02-07T22:30:00Z"
            }
        }


# ========== QUERY FILTERS ==========
class EventFilters(BaseModel):
    """Query parameters for filtering events"""
    zone_id: Optional[str] = None
    camera_id: Optional[str] = None
    object_type: Optional[ObjectType] = None
    status: Optional[EventStatus] = None
    threat_level: Optional[ThreatLevel] = None
    
    # Time range
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Pagination
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=1000)
    
    # Sorting
    sort_by: str = Field("detected_at", pattern="^(detected_at|threat_score|created_at)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


# ========== STATISTICS ==========
class EventStats(BaseModel):
    """Event statistics for dashboard"""
    total_events: int
    critical_threats: int
    high_threats: int
    medium_threats: int
    low_threats: int
    
    # By status
    new_events: int
    investigating: int
    resolved: int
    
    # Top zones
    top_zones: List[dict] = Field(default_factory=list)
    
    # Time distribution
    hourly_distribution: dict = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_events": 247,
                "critical_threats": 12,
                "high_threats": 45,
                "medium_threats": 98,
                "low_threats": 92,
                "new_events": 23,
                "investigating": 8,
                "resolved": 216,
                "top_zones": [
                    {"zone_id": "Z001", "zone_name": "Main Entrance", "count": 67},
                    {"zone_id": "Z004", "zone_name": "Perimeter", "count": 54}
                ],
                "hourly_distribution": {
                    "22": 34,
                    "23": 28,
                    "00": 19
                }
            }
        }
