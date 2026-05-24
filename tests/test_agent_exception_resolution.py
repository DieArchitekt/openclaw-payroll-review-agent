import pandas as pd

from processors.audit_log_v1 import audit_log_path
from processors.exception_resolution_v1 import (
    RESOLUTION_ACCEPTED,
    ExceptionResolution,
    add_anomaly_ids,
    apply_exception_resolutions,
)


def test_exception_resolution_keeps_original_anomaly_and_adds_resolution(tmp_path):
    review_id = "REV-EXCEPTION"
    anomalies_df = add_anomaly_ids(
        pd.DataFrame(
            [
                {
                    "Severity": "HIGH",
                    "Category": "High NetPay",
                    "Employee": "Ada Lovelace",
                    "Field": "NetPay",
                    "Current Value": 12000.0,
                    "Previous Value": 9000.0,
                    "Change %": 33.3,
                    "Message": "NetPay is above threshold.",
                }
            ]
        )
    )
    resolution = ExceptionResolution(
        review_id=review_id,
        anomaly_id=anomalies_df.iloc[0]["Anomaly ID"],
        status=RESOLUTION_ACCEPTED,
        reason="Confirmed director payment.",
        resolved_by="Finance Manager",
    )

    resolved = apply_exception_resolutions(
        anomalies_df,
        [resolution],
        audit_root=tmp_path,
    )

    assert len(resolved) == 1
    assert resolved.iloc[0]["Severity"] == "HIGH"
    assert resolved.iloc[0]["Resolution Status"] == RESOLUTION_ACCEPTED
    assert resolved.iloc[0]["Resolution Reason"] == "Confirmed director payment."
    assert audit_log_path(review_id, tmp_path).exists()
