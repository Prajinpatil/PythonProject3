"""
System Constants - Surveillance Intelligence Engine
Defines all fixed values, thresholds, and threat weights
"""

# ========== THREAT SCORING WEIGHTS ==========
OBJECT_WEIGHTS = {
    "human": 40,
    "vehicle": 60,
    "animal": 5,
    "drone": 70,
    "weapon": 95,
    "bag": 30,
    "package": 25,
    "unknown": 20
}

# ========== TIME-BASED MODIFIERS ==========
TIME_MULTIPLIERS = {
    "night": 1.8,      # 10 PM - 6 AM (High risk)
    "dawn": 1.3,       # 6 AM - 8 AM (Medium risk)
    "day": 1.0,        # 8 AM - 6 PM (Normal)
    "dusk": 1.4,       # 6 PM - 10 PM (Medium-high risk)
}

# ========== ZONE SENSITIVITY LEVELS ==========
ZONE_MULTIPLIERS = {
    "critical": 2.0,    # Server rooms, vaults
    "restricted": 1.5,  # Executive areas, labs
    "controlled": 1.2,  # Office spaces
    "public": 1.0,      # Lobbies, common areas
    "perimeter": 1.3    # Fences, gates
}

# ========== ALERT THRESHOLDS ==========
THREAT_LEVELS = {
    "critical": 80,     # Immediate response
    "high": 60,         # Quick response
    "medium": 40,       # Monitor closely
    "low": 20,          # Log only
    "minimal": 0        # Ignore
}

# ========== PATTERN DETECTION ==========
PATTERN_THRESHOLDS = {
    "repeat_intrusion_count": 3,      # Same zone, same object type
    "time_window_minutes": 30,        # Within this window = pattern
    "zone_cluster_radius": 50,        # meters
    "frequency_threshold": 5          # events per hour = high frequency
}

# ========== ANALYTICS WINDOWS ==========
ANALYTICS_WINDOWS = {
    "recent": 3600,        # Last 1 hour (seconds)
    "daily": 86400,        # Last 24 hours
    "weekly": 604800,      # Last 7 days
    "monthly": 2592000     # Last 30 days
}

# ========== SYSTEM LIMITS ==========
MAX_EVENTS_PER_REQUEST = 1000
MAX_CAMERAS_PER_ZONE = 20
EVENT_RETENTION_DAYS = 90
ALERT_COOLDOWN_SECONDS = 300  # Don't spam same alert

# ========== API SECURITY ==========
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
REFRESH_TOKEN_EXPIRE_DAYS = 7
RATE_LIMIT_PER_MINUTE = 100

# ========== CAMERA STATUSES ==========
CAMERA_STATUS = {
    "active": "ACTIVE",
    "offline": "OFFLINE",
    "maintenance": "MAINTENANCE",
    "error": "ERROR"
}

# ========== EVENT STATUSES ==========
EVENT_STATUS = {
    "new": "NEW",
    "investigating": "INVESTIGATING",
    "resolved": "RESOLVED",
    "false_positive": "FALSE_POSITIVE",
    "escalated": "ESCALATED"
}

# ========== USER ROLES ==========
ROLES = {
    "admin": "ADMIN",
    "operator": "OPERATOR",
    "viewer": "VIEWER",
    "analyst": "ANALYST"
}

ROLE_PERMISSIONS = {
    "ADMIN": ["read", "write", "delete", "configure", "manage_users"],
    "OPERATOR": ["read", "write", "acknowledge_alerts"],
    "ANALYST": ["read", "generate_reports", "view_analytics"],
    "VIEWER": ["read"]
}

# ========== NOTIFICATION SETTINGS ==========
NOTIFICATION_CHANNELS = {
    "email": True,
    "sms": True,
    "webhook": True,
    "dashboard": True
}

# ========== DEMO/TEST DATA ==========
DEFAULT_ZONES = [
    {"id": "Z001", "name": "Main Entrance", "sensitivity": "critical"},
    {"id": "Z002", "name": "Parking Lot", "sensitivity": "controlled"},
    {"id": "Z003", "name": "Server Room", "sensitivity": "critical"},
    {"id": "Z004", "name": "Perimeter Fence", "sensitivity": "perimeter"},
    {"id": "Z005", "name": "Lobby", "sensitivity": "public"}
]

DEFAULT_CAMERAS = [
    {"id": "CAM001", "zone_id": "Z001", "name": "Entrance-Front", "status": "ACTIVE"},
    {"id": "CAM002", "zone_id": "Z002", "name": "Parking-North", "status": "ACTIVE"},
    {"id": "CAM003", "zone_id": "Z003", "name": "Server-Room-1", "status": "ACTIVE"},
    {"id": "CAM004", "zone_id": "Z004", "name": "Fence-East", "status": "ACTIVE"},
    {"id": "CAM005", "zone_id": "Z005", "name": "Lobby-Center", "status": "ACTIVE"}
]
