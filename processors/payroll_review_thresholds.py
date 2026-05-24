from processors.anomaly_detector_v1.constants import (
    BACS_TOLERANCE,
    HIGH_NET_PAY_THRESHOLD,
    LOW_NI_TO_GROSS_RATIO,
    LOW_PAYE_TO_GROSS_RATIO,
)

THRESHOLD_VARIANCE = "variance_threshold"
THRESHOLD_HIGH_NET_PAY = "high_net_pay_threshold"
THRESHOLD_LOW_PAYE_RATIO = "low_paye_ratio"
THRESHOLD_LOW_NI_RATIO = "low_ni_ratio"
THRESHOLD_BACS_TOLERANCE = "bacs_tolerance"

PROTECTED_THRESHOLDS = {
    THRESHOLD_VARIANCE,
    THRESHOLD_HIGH_NET_PAY,
    THRESHOLD_LOW_PAYE_RATIO,
    THRESHOLD_LOW_NI_RATIO,
    THRESHOLD_BACS_TOLERANCE,
}


def default_thresholds(variance_threshold: float) -> dict[str, float]:
    return {
        THRESHOLD_VARIANCE: float(variance_threshold),
        THRESHOLD_HIGH_NET_PAY: HIGH_NET_PAY_THRESHOLD,
        THRESHOLD_LOW_PAYE_RATIO: LOW_PAYE_TO_GROSS_RATIO,
        THRESHOLD_LOW_NI_RATIO: LOW_NI_TO_GROSS_RATIO,
        THRESHOLD_BACS_TOLERANCE: BACS_TOLERANCE,
    }
