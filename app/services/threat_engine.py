"""
Threat Engine - Intelligence Core
Calculates threat scores using multi-factor analysis
This is the system's competitive advantage
"""

from datetime import datetime
from typing import Dict, Any
import logging

from app.core.constants import (
    OBJECT_WEIGHTS,
    TIME_MULTIPLIERS,
    ZONE_MULTIPLIERS,
    THREAT_LEVELS
)
from app.utils.time_utils import classify_time_of_day, is_business_hours, is_weekend
from app.schemas.event_schema import ThreatLevel

logger = logging.getLogger(__name__)


class ThreatScoringEngine:
    """
    Advanced threat scoring system
    Combines multiple factors for intelligent threat assessment
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_threat_score(
        self,
        object_type: str,
        zone_sensitivity: str,
        confidence: float,
        detected_at: datetime,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Master threat calculation function
        
        Returns dict with:
            - threat_score (0-100)
            - threat_level (critical/high/medium/low)
            - breakdown (component scores for explainability)
        """
        
        metadata = metadata or {}
        
        # ========== COMPONENT 1: Base Object Weight ==========
        base_weight = OBJECT_WEIGHTS.get(object_type, 20)
        
        # ========== COMPONENT 2: Detection Confidence ==========
        confidence_multiplier = confidence  # 0.0 to 1.0
        
        # ========== COMPONENT 3: Time-based Risk ==========
        time_period = classify_time_of_day(detected_at)
        time_multiplier = TIME_MULTIPLIERS.get(time_period, 1.0)
        
        # ========== COMPONENT 4: Zone Sensitivity ==========
        zone_multiplier = ZONE_MULTIPLIERS.get(zone_sensitivity, 1.0)
        
        # ========== COMPONENT 5: Contextual Factors ==========
        context_multiplier = self._calculate_context_multiplier(
            detected_at,
            metadata
        )
        
        # ========== FINAL CALCULATION ==========
        raw_score = (
            base_weight * 
            confidence_multiplier * 
            time_multiplier * 
            zone_multiplier * 
            context_multiplier
        )
        
        # Normalize to 0-100 scale
        threat_score = min(100.0, raw_score)
        
        # Determine threat level
        threat_level = self._determine_threat_level(threat_score)
        
        # Build explainable breakdown
        breakdown = {
            "base_object_weight": base_weight,
            "confidence": confidence,
            "time_period": time_period,
            "time_multiplier": time_multiplier,
            "zone_sensitivity": zone_sensitivity,
            "zone_multiplier": zone_multiplier,
            "context_multiplier": context_multiplier,
            "raw_score": round(raw_score, 2)
        }
        
        self.logger.info(
            f"Threat calculated: {threat_score:.2f} ({threat_level}) - "
            f"Object: {object_type}, Zone: {zone_sensitivity}, Time: {time_period}"
        )
        
        return {
            "threat_score": round(threat_score, 2),
            "threat_level": threat_level,
            "breakdown": breakdown
        }
    
    def _calculate_context_multiplier(
        self,
        detected_at: datetime,
        metadata: Dict[str, Any]
    ) -> float:
        """
        Additional context-based scoring
        Accounts for business hours, weekends, etc.
        """
        multiplier = 1.0
        
        # Outside business hours = higher risk
        if not is_business_hours(detected_at):
            multiplier *= 1.3
        
        # Weekend intrusions more suspicious
        if is_weekend(detected_at):
            multiplier *= 1.2
        
        # Check metadata for additional context
        direction = metadata.get("direction", "")
        if direction == "entering":
            multiplier *= 1.1  # Entering more concerning than leaving
        
        count = metadata.get("count", 1)
        if count > 1:
            # Multiple objects = higher threat
            multiplier *= (1.0 + (count - 1) * 0.1)
        
        # Check for loitering behavior
        if metadata.get("loitering", False):
            multiplier *= 1.4
        
        # Check for repeated zone entries
        if metadata.get("repeat_entry", False):
            multiplier *= 1.3
        
        return min(multiplier, 2.5)  # Cap at 2.5x
    
    def _determine_threat_level(self, score: float) -> str:
        """
        Convert numeric score to categorical threat level
        """
        if score >= THREAT_LEVELS["critical"]:
            return ThreatLevel.critical.value
        elif score >= THREAT_LEVELS["high"]:
            return ThreatLevel.high.value
        elif score >= THREAT_LEVELS["medium"]:
            return ThreatLevel.medium.value
        elif score >= THREAT_LEVELS["low"]:
            return ThreatLevel.low.value
        else:
            return ThreatLevel.minimal.value
    
    def should_trigger_alert(
        self,
        threat_score: float,
        zone_sensitivity: str
    ) -> bool:
        """
        Decide if event should trigger immediate alert
        
        Rules:
        - Critical zones: alert on medium+ threats
        - Other zones: alert on high+ threats
        """
        if zone_sensitivity == "critical":
            return threat_score >= THREAT_LEVELS["medium"]
        elif zone_sensitivity == "restricted":
            return threat_score >= THREAT_LEVELS["high"]
        else:
            return threat_score >= THREAT_LEVELS["critical"]
    
    def assess_multiple_events(
        self,
        events: list
    ) -> Dict[str, Any]:
        """
        Analyze multiple related events for pattern escalation
        Used for detecting coordinated intrusions
        """
        if not events:
            return {"escalated": False, "reason": None}
        
        # Check for rapid succession
        if len(events) >= 3:
            time_diffs = []
            for i in range(1, len(events)):
                diff = (events[i]["detected_at"] - events[i-1]["detected_at"]).total_seconds()
                time_diffs.append(diff)
            
            avg_interval = sum(time_diffs) / len(time_diffs)
            
            if avg_interval < 60:  # Less than 1 minute apart
                return {
                    "escalated": True,
                    "reason": "Rapid succession events detected",
                    "interval_seconds": avg_interval
                }
        
        # Check for multiple high-value objects
        high_value_objects = ["drone", "weapon", "vehicle"]
        high_value_count = sum(
            1 for e in events 
            if e.get("object_type") in high_value_objects
        )
        
        if high_value_count >= 2:
            return {
                "escalated": True,
                "reason": "Multiple high-value objects detected"
            }
        
        return {"escalated": False}


# ========== SINGLETON INSTANCE ==========
threat_engine = ThreatScoringEngine()


# ========== HELPER FUNCTIONS ==========
def calculate_threat(
    object_type: str,
    zone_sensitivity: str,
    confidence: float,
    detected_at: datetime = None,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Convenience function for threat calculation
    """
    detected_at = detected_at or datetime.utcnow()
    return threat_engine.calculate_threat_score(
        object_type=object_type,
        zone_sensitivity=zone_sensitivity,
        confidence=confidence,
        detected_at=detected_at,
        metadata=metadata
    )


def should_alert(threat_score: float, zone_sensitivity: str) -> bool:
    """Convenience function for alert decision"""
    return threat_engine.should_trigger_alert(threat_score, zone_sensitivity)
