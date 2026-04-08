# thresholds.py — defines severity classification thresholds for all Amazon account health metrics.
# Classifier (controllers/classifier.py) imports these constants — do not hardcode values there.

# Severity label constants
# #note: String constants used across the app to represent the three severity levels
CRITICAL: str = "critical"
WARNING: str = "warning"
HEALTHY: str = "healthy"
UNKNOWN: str = "unknown"

# Late Shipment Rate thresholds (percentage)
# #note: Amazon flags sellers at >= 4% late shipment rate as at-risk
LATE_SHIPMENT_CRITICAL: float = 4.0
LATE_SHIPMENT_WARNING: float = 2.0

# Valid Tracking Rate thresholds (percentage)
# #note: Below 95% is critical; Amazon requires > 98% for healthy status
VALID_TRACKING_CRITICAL: float = 95.0
VALID_TRACKING_WARNING: float = 98.0

# Pre-fulfillment Cancel Rate thresholds (percentage)
# #note: Amazon policy violation at >= 2.5%; warning zone starts at 1%
PRE_CANCEL_CRITICAL: float = 2.5
PRE_CANCEL_WARNING: float = 1.0

# Order Defect Rate (ODR) thresholds (percentage)
# #note: ODR >= 1% can result in account suspension; warning starts at 0.5%
ODR_CRITICAL: float = 1.0
ODR_WARNING: float = 0.5

# Account Health Rating (AHR) thresholds (integer score)
# #note: Amazon AHR score — lower is worse; <= 250 is at risk of deactivation
AHR_CRITICAL: int = 250
AHR_WARNING: int = 300

# Account status strings that map to critical
# #note: Any of these account status values triggers a critical alert
CRITICAL_ACCOUNT_STATUSES: list[str] = ["AT_RISK", "DEACTIVATED", "SUSPENDED"]
