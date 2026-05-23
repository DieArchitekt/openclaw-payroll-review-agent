import pandas as pd


def percent_change(
    current: pd.Series | float, previous: pd.Series | float
) -> pd.Series | float:
    """Return percentage change using previous value as the base."""
    if isinstance(previous, pd.Series):
        result: pd.Series = (
            (current - previous).where(previous != 0, 0.0)
            / previous.where(previous != 0, pd.NA)
            * 100
        )
        return result.fillna(0.0)

    return 0.0 if previous == 0 else ((current - previous) / previous) * 100
