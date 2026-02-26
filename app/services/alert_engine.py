"""
Alert Engine - Notification & Alert Management
Decides when to alert, prevents spam, manages alert lifecycle
"""

from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import logging

from app.core.constants import ALERT_COOLDOWN_SECONDS, THREAT_LEVELS
from app.schemas.alert_schema import AlertPriority
from app.utils.time_utils import is_within_cooldown

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Smart alert management system
    Prevents alert fatigue while ensuring critical events are flagged
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # In-memory cooldown tracker (use Redis/DB in production)
        self.alert_cooldowns = {}
    
    def should_create_alert(
        self,
        event_data: Dict[str, Any],
        zone_sensitivity: str
    ) -> Dict[str, bool]:
        """
        Intelligent alert decision
        
        Factors:
        - Threat score
        - Zone sensitivity
        - Recent alerts (cooldown)
        - Time of day
        
        Returns:
            {
                "should_alert": bool,
                "priority": str,
                "reason": str
            }
        """
        threat_score = event_data.get("threat_score", 0)
        threat_level = event_data.get("threat_level", "low")
        zone_id = event_data.get("zone_id")
        object_type = event_data.get("object_type")
        
        # Check cooldown
        cooldown_key = f"{zone_id}_{object_type}"
        if self._is_in_cooldown(cooldown_key):
            return {
                "should_alert": False,
                "priority": None,
                "reason": "Alert cooldown active for this zone/object combination"
            }
        
        # Decision logic
        if threat_level == "critical":
            # Always alert on critical
            priority = AlertPriority.critical
            should_alert = True
            reason = "Critical threat detected"
        
        elif threat_level == "high":
            # Alert on high threats in sensitive zones
            if zone_sensitivity in ["critical", "restricted"]:
                priority = AlertPriority.high
                should_alert = True
                reason = "High threat in sensitive zone"
            else:
                priority = AlertPriority.medium
                should_alert = True
                reason = "High threat detected"
        
        elif threat_level == "medium":
            # Only alert in critical zones
            if zone_sensitivity == "critical":
                priority = AlertPriority.medium
                should_alert = True
                reason = "Medium threat in critical zone"
            else:
                should_alert = False
                priority = None
                reason = "Below alert threshold"
        
        else:
            # Low threats don't trigger alerts
            should_alert = False
            priority = None
            reason = "Below alert threshold"
        
        # Set cooldown if alerting
        if should_alert:
            self._set_cooldown(cooldown_key)
        
        return {
            "should_alert": should_alert,
            "priority": priority.value if priority else None,
            "reason": reason
        }
    
    def generate_alert_message(
        self,
        event_data: Dict[str, Any],
        zone_name: Optional[str] = None
    ) -> str:
        """
        Create human-readable alert message
        """
        object_type = event_data.get("object_type", "unknown object")
        zone = zone_name or event_data.get("zone_id", "unknown zone")
        threat_level = event_data.get("threat_level", "unknown")
        threat_score = event_data.get("threat_score", 0)
        time_period = event_data.get("metadata", {}).get("time_period", "")
        
        # Build contextual message
        messages = {
            "critical": f"🚨 CRITICAL ALERT: {object_type.title()} detected in {zone} (Score: {threat_score:.0f})",
            "high": f"⚠️  HIGH ALERT: {object_type.title()} detected in {zone} (Score: {threat_score:.0f})",
            "medium": f"⚡ MEDIUM ALERT: {object_type.title()} detected in {zone} (Score: {threat_score:.0f})",
            "low": f"ℹ️  LOW ALERT: {object_type.title()} detected in {zone} (Score: {threat_score:.0f})"
        }
        
        message = messages.get(threat_level, f"Event detected: {object_type} in {zone}")
        
        # Add time context
        if time_period and time_period != "day":
            message += f" during {time_period}"
        
        return message
    
    def _is_in_cooldown(self, key: str) -> bool:
        """Check if alert cooldown is active"""
        if key not in self.alert_cooldowns:
            return False
        
        last_alert_time = self.alert_cooldowns[key]
        return is_within_cooldown(last_alert_time, ALERT_COOLDOWN_SECONDS)
    
    def _set_cooldown(self, key: str):
        """Set cooldown for zone/object combination"""
        self.alert_cooldowns[key] = datetime.utcnow()
    
    def clear_cooldown(self, key: str):
        """Manually clear cooldown (for testing)"""
        if key in self.alert_cooldowns:
            del self.alert_cooldowns[key]
    
    def get_active_cooldowns(self) -> Dict[str, datetime]:
        """Get all active cooldowns (for debugging)"""
        now = datetime.utcnow()
        return {
            key: last_time
            for key, last_time in self.alert_cooldowns.items()
            if (now - last_time).total_seconds() < ALERT_COOLDOWN_SECONDS
        }
    
    def calculate_alert_priority(self, threat_score: float) -> str:
        """
        Map threat score to alert priority
        """
        if threat_score >= THREAT_LEVELS["critical"]:
            return AlertPriority.critical.value
        elif threat_score >= THREAT_LEVELS["high"]:
            return AlertPriority.high.value
        elif threat_score >= THREAT_LEVELS["medium"]:
            return AlertPriority.medium.value
        else:
            return AlertPriority.low.value
    
    def should_escalate(
        self,
        alert_data: Dict[str, Any],
        time_since_creation: timedelta
    ) -> bool:
        """
        Determine if unresolved alert should be escalated
        
        Escalation rules:
        - Critical alerts: escalate after 5 minutes
        - High alerts: escalate after 15 minutes
        - Medium alerts: escalate after 30 minutes
        """
        priority = alert_data.get("priority", "LOW")
        
        escalation_times = {
            "CRITICAL": 300,   # 5 minutes
            "HIGH": 900,       # 15 minutes
            "MEDIUM": 1800,    # 30 minutes
            "LOW": 3600        # 1 hour
        }
        
        threshold = escalation_times.get(priority, 3600)
        return time_since_creation.total_seconds() >= threshold


# ========== SINGLETON INSTANCE ==========
alert_engine = AlertEngine()


# ========== HELPER FUNCTIONS ==========
def should_alert(event_data: Dict[str, Any], zone_sensitivity: str) -> Dict[str, Any]:
    """Convenience function"""
    return alert_engine.should_create_alert(event_data, zone_sensitivity)


def create_alert_message(event_data: Dict[str, Any], zone_name: str = None) -> str:
    """Convenience function"""
    return alert_engine.generate_alert_message(event_data, zone_name)
