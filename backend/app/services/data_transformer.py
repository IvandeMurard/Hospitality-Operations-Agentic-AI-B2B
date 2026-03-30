import pandas as pd
from typing import List, Dict, Any
from datetime import datetime

# Home country for the pilot property — bookings from other countries are
# counted as "international" when computing intl_guest_ratio.
_HOME_COUNTRY = "FR"

# Arrival-time scoring: maps hour-of-day buckets to a F&B relevance score.
# Early-morning arrivals (0-11) rarely drive same-day dinner covers, while
# peak check-in hours (14-18) correlate with higher dinner demand.
_ARRIVAL_HOUR_SCORES: Dict[int, float] = {
    0: 0.1, 1: 0.1, 2: 0.1, 3: 0.1, 4: 0.1, 5: 0.1,
    6: 0.2, 7: 0.3, 8: 0.3, 9: 0.3, 10: 0.3, 11: 0.3,
    12: 0.5, 13: 0.6, 14: 0.8, 15: 0.9, 16: 1.0, 17: 1.0,
    18: 0.9, 19: 0.8, 20: 0.7, 21: 0.6, 22: 0.5, 23: 0.3,
}


class DataTransformer:
    """
    Utility to transform PMS raw data into ML-ready formats.
    Focus: Apaleo Stay Records to Prophet (ds, y).
    """

    @staticmethod
    def stay_records_to_prophet(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Aggregates guest counts by date for Prophet training.
        """
        if not records:
            return pd.DataFrame(columns=['ds', 'y'])

        data = []
        for rec in records:
            arrival = rec.get("arrival", "")
            # Arrival usually comes as ISO string
            if arrival:
                ds = arrival[:10] # Extract YYYY-MM-DD
                # Summing up total guests (adults + children) as a proxy for covers
                total_guests = rec.get("adults", 0) + rec.get("children", 0)
                data.append({"ds": ds, "y": total_guests})

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame(columns=['ds', 'y'])

        # Group by date to get daily totals
        df['ds'] = pd.to_datetime(df['ds'])
        daily_df = df.groupby('ds')['y'].sum().reset_index()

        return daily_df

    @staticmethod
    def add_external_features(df: pd.DataFrame, weather_data: Dict[str, float]) -> pd.DataFrame:
        """
        Joins external features (e.g. weather score) for multivariable forecasting.
        """
        # Simplification: Applying same weather score or joining on date
        df['weather_score'] = df['ds'].map(lambda x: weather_data.get(x.strftime('%Y-%m-%d'), 0.5))
        return df

    # ------------------------------------------------------------------
    # HOS-106 — Contextual forecasting features (EHL Cindy Heo)
    # These four signals are first-class Prophet regressors, not metadata.
    # ------------------------------------------------------------------

    @staticmethod
    def extract_contextual_features(records: List[Dict[str, Any]]) -> pd.DataFrame:
        """Extract per-date contextual features from PMS stay records.

        Returns a DataFrame with columns:
          ds                 — date (datetime64)
          avg_los            — average length of stay in nights (float)
          avg_party_size     — average (adults + children) per reservation (float)
          intl_guest_ratio   — fraction of reservations with origin_country != HOME_COUNTRY (0-1)
          arrival_time_score — mean F&B relevance of arrival hour (0-1)

        All four columns are suitable for direct use as Prophet additional
        regressors alongside weather_score, event_impact, and occupancy.
        """
        if not records:
            return pd.DataFrame(
                columns=["ds", "avg_los", "avg_party_size", "intl_guest_ratio", "arrival_time_score"]
            )

        rows = []
        for rec in records:
            arrival_raw = rec.get("arrival", "")
            if not arrival_raw:
                continue

            ds_str = arrival_raw[:10]  # YYYY-MM-DD

            # Length of Stay (nights)
            departure_raw = rec.get("departure", "")
            los: float = 1.0
            if departure_raw and len(departure_raw) >= 10:
                try:
                    arr_dt = datetime.fromisoformat(arrival_raw[:10])
                    dep_dt = datetime.fromisoformat(departure_raw[:10])
                    delta = (dep_dt - arr_dt).days
                    los = max(1.0, float(delta))
                except ValueError:
                    los = 1.0

            # Party size
            party_size = float(rec.get("adults", 1) + rec.get("children", 0))
            party_size = max(1.0, party_size)

            # International guest flag
            origin = rec.get("origin_country", _HOME_COUNTRY) or _HOME_COUNTRY
            is_intl = 0.0 if origin.upper() == _HOME_COUNTRY else 1.0

            # Arrival-time score (hour-of-day → F&B relevance)
            arrival_time_score = 0.5  # default when time unavailable
            if len(arrival_raw) >= 13:  # ISO string has at least HH portion
                try:
                    hour = int(arrival_raw[11:13])
                    arrival_time_score = _ARRIVAL_HOUR_SCORES.get(hour, 0.5)
                except (ValueError, IndexError):
                    pass

            rows.append({
                "ds": ds_str,
                "los": los,
                "party_size": party_size,
                "is_intl": is_intl,
                "arrival_time_score": arrival_time_score,
            })

        if not rows:
            return pd.DataFrame(
                columns=["ds", "avg_los", "avg_party_size", "intl_guest_ratio", "arrival_time_score"]
            )

        df = pd.DataFrame(rows)
        df["ds"] = pd.to_datetime(df["ds"])

        agg = (
            df.groupby("ds")
            .agg(
                avg_los=("los", "mean"),
                avg_party_size=("party_size", "mean"),
                intl_guest_ratio=("is_intl", "mean"),
                arrival_time_score=("arrival_time_score", "mean"),
            )
            .reset_index()
        )
        return agg

    @staticmethod
    def merge_contextual_features(
        prophet_df: pd.DataFrame,
        contextual_df: pd.DataFrame,
    ) -> pd.DataFrame:
        """Left-join contextual features onto the prophet training DataFrame.

        Missing dates (no stay records) are filled with neutral defaults so
        Prophet can still train without gaps:
          avg_los            → 2.0 (typical city-hotel LOS)
          avg_party_size     → 1.5
          intl_guest_ratio   → 0.3
          arrival_time_score → 0.5
        """
        if contextual_df.empty:
            prophet_df["avg_los"] = 2.0
            prophet_df["avg_party_size"] = 1.5
            prophet_df["intl_guest_ratio"] = 0.3
            prophet_df["arrival_time_score"] = 0.5
            return prophet_df

        merged = prophet_df.merge(contextual_df, on="ds", how="left")
        merged["avg_los"] = merged["avg_los"].fillna(2.0)
        merged["avg_party_size"] = merged["avg_party_size"].fillna(1.5)
        merged["intl_guest_ratio"] = merged["intl_guest_ratio"].fillna(0.3)
        merged["arrival_time_score"] = merged["arrival_time_score"].fillna(0.5)
        return merged
