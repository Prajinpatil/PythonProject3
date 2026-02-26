"""
Analytics Engine - Pattern Detection & Intelligence
Identifies trends, hotspots, and behavioral patterns
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from collections import defaultdict, Counter
import logging

from app.core.constants import PATTERN_THRESHOLDS, ANALYTICS_WINDOWS
from app.utils.time_utils import get_recent_window, get_daily_window, get_hour_of_day

logger = logging.getLogger(__name__)


class AnalyticsEngine:
    """
    Advanced analytics for surveillance intelligence
    Detects patterns, anomalies, and provides actionable insights
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Comprehensive pattern detection across events
        
        Returns:
            - repeat_intrusions: Same zone/object combinations
            - temporal_clusters: Time-based groupings
            - zone_hotspots: High-activity zones
            - anomalies: Unusual patterns
        """
        if not events:
            return self._empty_pattern_result()
        
        patterns = {
            "repeat_intrusions": self._detect_repeat_intrusions(events),
            "temporal_clusters": self._detect_temporal_patterns(events),
            "zone_hotspots": self._detect_zone_hotspots(events),
            "object_frequency": self._analyze_object_frequency(events),
            "time_distribution": self._analyze_time_distribution(events)
        }
        
        return patterns
    
    def _detect_repeat_intrusions(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find repeated intrusions in same zone with same object type
        Pattern: 3+ events, same zone+object, within 30 min
        """
        patterns = []
        
        # Group by zone and object type
        groups = defaultdict(list)
        for event in events:
            key = (event.get("zone_id"), event.get("object_type"))
            groups[key].append(event)
        
        # Check each group for patterns
        for (zone_id, object_type), group_events in groups.items():
            if len(group_events) < PATTERN_THRESHOLDS["repeat_intrusion_count"]:
                continue
            
            # Sort by time
            sorted_events = sorted(group_events, key=lambda e: e.get("detected_at"))
            
            # Check time window
            time_window = timedelta(minutes=PATTERN_THRESHOLDS["time_window_minutes"])
            
            for i in range(len(sorted_events) - 2):
                window_events = []
                start_time = sorted_events[i]["detected_at"]
                
                for event in sorted_events[i:]:
                    if event["detected_at"] <= start_time + time_window:
                        window_events.append(event)
                    else:
                        break
                
                if len(window_events) >= PATTERN_THRESHOLDS["repeat_intrusion_count"]:
                    patterns.append({
                        "pattern_type": "repeat_intrusion",
                        "zone_id": zone_id,
                        "object_type": object_type,
                        "event_count": len(window_events),
                        "time_span_minutes": (
                            window_events[-1]["detected_at"] - window_events[0]["detected_at"]
                        ).total_seconds() / 60,
                        "first_event": window_events[0]["event_id"],
                        "last_event": window_events[-1]["event_id"],
                        "severity": "high" if len(window_events) >= 5 else "medium"
                    })
                    break
        
        return patterns
    
    def _detect_temporal_patterns(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze time-based patterns
        Peak hours, unusual activity times
        """
        hourly_counts = defaultdict(int)
        daily_counts = defaultdict(int)
        
        for event in events:
            dt = event.get("detected_at")
            if not dt:
                continue
            
            hourly_counts[dt.hour] += 1
            daily_counts[dt.strftime("%Y-%m-%d")] += 1
        
        # Find peak hour
        peak_hour = max(hourly_counts.items(), key=lambda x: x[1]) if hourly_counts else (0, 0)
        
        # Find unusual hours (outside 8 AM - 6 PM)
        unusual_hours = {
            hour: count 
            for hour, count in hourly_counts.items() 
            if (hour < 8 or hour >= 18) and count > 0
        }
        
        return {
            "hourly_distribution": dict(hourly_counts),
            "daily_distribution": dict(daily_counts),
            "peak_hour": peak_hour[0],
            "peak_hour_count": peak_hour[1],
            "unusual_hour_activity": unusual_hours,
            "total_unusual_hour_events": sum(unusual_hours.values())
        }
    
    def _detect_zone_hotspots(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Identify high-activity zones
        """
        zone_counts = Counter(event.get("zone_id") for event in events)
        zone_threats = defaultdict(list)
        
        for event in events:
            zone_id = event.get("zone_id")
            threat_score = event.get("threat_score", 0)
            zone_threats[zone_id].append(threat_score)
        
        hotspots = []
        for zone_id, count in zone_counts.most_common(10):
            avg_threat = sum(zone_threats[zone_id]) / len(zone_threats[zone_id])
            
            hotspots.append({
                "zone_id": zone_id,
                "event_count": count,
                "avg_threat_score": round(avg_threat, 2),
                "max_threat_score": round(max(zone_threats[zone_id]), 2),
                "risk_level": "high" if avg_threat >= 60 else "medium" if avg_threat >= 40 else "low"
            })
        
        return hotspots
    
    def _analyze_object_frequency(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze object type frequencies
        """
        object_counts = Counter(event.get("object_type") for event in events)
        
        return {
            "distribution": dict(object_counts),
            "most_common": object_counts.most_common(5),
            "unique_types": len(object_counts)
        }
    
    def _analyze_time_distribution(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze when events occur
        """
        time_periods = Counter()
        
        for event in events:
            dt = event.get("detected_at")
            if not dt:
                continue
            
            hour = dt.hour
            if 6 <= hour < 12:
                time_periods["morning"] += 1
            elif 12 <= hour < 18:
                time_periods["afternoon"] += 1
            elif 18 <= hour < 22:
                time_periods["evening"] += 1
            else:
                time_periods["night"] += 1
        
        return dict(time_periods)
    
    def _empty_pattern_result(self) -> Dict[str, Any]:
        """Return empty pattern structure"""
        return {
            "repeat_intrusions": [],
            "temporal_clusters": {},
            "zone_hotspots": [],
            "object_frequency": {},
            "time_distribution": {}
        }
    
    def generate_risk_assessment(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comprehensive risk assessment report
        """
        if not events:
            return {
                "overall_risk": "low",
                "risk_score": 0,
                "summary": "No recent activity"
            }
        
        # Calculate metrics
        total_events = len(events)
        critical_count = sum(1 for e in events if e.get("threat_level") == "critical")
        high_count = sum(1 for e in events if e.get("threat_level") == "high")
        
        avg_threat = sum(e.get("threat_score", 0) for e in events) / total_events
        
        # Determine overall risk
        if critical_count >= 3 or avg_threat >= 70:
            overall_risk = "critical"
        elif high_count >= 5 or avg_threat >= 55:
            overall_risk = "high"
        elif avg_threat >= 40:
            overall_risk = "medium"
        else:
            overall_risk = "low"
        
        # Get patterns
        patterns = self.detect_patterns(events)
        
        return {
            "overall_risk": overall_risk,
            "risk_score": round(avg_threat, 2),
            "total_events": total_events,
            "critical_events": critical_count,
            "high_events": high_count,
            "patterns_detected": len(patterns.get("repeat_intrusions", [])),
            "top_zones": patterns.get("zone_hotspots", [])[:3],
            "summary": self._generate_summary(overall_risk, total_events, critical_count)
        }
    
    def _generate_summary(self, risk: str, total: int, critical: int) -> str:
        """Generate human-readable summary"""
        summaries = {
            "critical": f"CRITICAL: {total} events with {critical} critical threats. Immediate action required.",
            "high": f"HIGH: {total} events detected. Enhanced monitoring recommended.",
            "medium": f"MEDIUM: {total} events detected. Standard monitoring in effect.",
            "low": f"LOW: {total} events detected. Normal activity levels."
        }
        return summaries.get(risk, "Activity detected")


# ========== SINGLETON INSTANCE ==========
analytics_engine = AnalyticsEngine()


# ========== HELPER FUNCTIONS ==========
def analyze_events(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for pattern detection"""
    return analytics_engine.detect_patterns(events)


def get_risk_assessment(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convenience function for risk assessment"""
    return analytics_engine.generate_risk_assessment(events)
