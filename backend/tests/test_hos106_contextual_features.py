"""Tests for HOS-106 — Contextual Forecasting Features.

Covers:
- DataTransformer.extract_contextual_features() — LOS, party_size,
  intl_guest_ratio, arrival_time_score derived from PMS stay records
- DataTransformer.merge_contextual_features() — left-join + fill defaults
- PredictionEngine.train() — registers new regressors when present in df
"""
from __future__ import annotations

import pandas as pd
import pytest

from app.services.data_transformer import DataTransformer


# ===========================================================================
# DataTransformer.extract_contextual_features
# ===========================================================================

class TestExtractContextualFeatures:

    def test_empty_records_returns_empty_dataframe(self):
        df = DataTransformer.extract_contextual_features([])
        assert df.empty
        assert list(df.columns) == [
            "ds", "avg_los", "avg_party_size", "intl_guest_ratio", "arrival_time_score"
        ]

    def test_single_record_basic_extraction(self):
        records = [{
            "arrival": "2026-03-01T14:00:00",
            "departure": "2026-03-03T11:00:00",
            "adults": 2,
            "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)

        assert len(df) == 1
        row = df.iloc[0]
        assert row["avg_los"] == pytest.approx(2.0)
        assert row["avg_party_size"] == pytest.approx(2.0)
        assert row["intl_guest_ratio"] == pytest.approx(0.0)
        # hour 14 maps to score 0.8
        assert row["arrival_time_score"] == pytest.approx(0.8)

    def test_international_guest_sets_ratio_to_one(self):
        records = [{
            "arrival": "2026-03-01T10:00:00",
            "departure": "2026-03-02T10:00:00",
            "adults": 2,
            "children": 0,
            "origin_country": "DE",  # international
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["intl_guest_ratio"] == pytest.approx(1.0)

    def test_mixed_domestic_international_ratio(self):
        """3 domestic + 1 international → intl_guest_ratio ≈ 0.25."""
        base = {
            "arrival": "2026-03-01T14:00:00",
            "departure": "2026-03-02T10:00:00",
            "adults": 2, "children": 0,
        }
        records = [
            {**base, "origin_country": "FR"},
            {**base, "origin_country": "FR"},
            {**base, "origin_country": "FR"},
            {**base, "origin_country": "GB"},
        ]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["intl_guest_ratio"] == pytest.approx(0.25)

    def test_los_minimum_one_night(self):
        """Same-day arrival/departure must not produce LOS < 1."""
        records = [{
            "arrival": "2026-03-01T14:00:00",
            "departure": "2026-03-01T16:00:00",
            "adults": 1, "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["avg_los"] >= 1.0

    def test_party_size_includes_children(self):
        records = [{
            "arrival": "2026-03-01T16:00:00",
            "departure": "2026-03-03T10:00:00",
            "adults": 2, "children": 2,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["avg_party_size"] == pytest.approx(4.0)

    def test_missing_arrival_time_uses_default_score(self):
        """When arrival has no time component, fall back to 0.5 score."""
        records = [{
            "arrival": "2026-03-01",  # no time
            "departure": "2026-03-03",
            "adults": 2, "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["arrival_time_score"] == pytest.approx(0.5)

    def test_peak_arrival_hour_scores_high(self):
        """Hour 16 (4 PM) is peak check-in → max score 1.0."""
        records = [{
            "arrival": "2026-03-01T16:30:00",
            "departure": "2026-03-03T10:00:00",
            "adults": 2, "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["arrival_time_score"] == pytest.approx(1.0)

    def test_early_morning_arrival_scores_low(self):
        """Hour 03 (3 AM) → minimum F&B relevance score 0.1."""
        records = [{
            "arrival": "2026-03-01T03:15:00",
            "departure": "2026-03-02T10:00:00",
            "adults": 1, "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["arrival_time_score"] == pytest.approx(0.1)

    def test_aggregates_multiple_arrivals_on_same_date(self):
        """Two records on the same date → averages are computed correctly."""
        records = [
            {
                "arrival": "2026-03-01T14:00:00",
                "departure": "2026-03-03T10:00:00",
                "adults": 2, "children": 0,
                "origin_country": "FR",
            },
            {
                "arrival": "2026-03-01T16:00:00",
                "departure": "2026-03-04T10:00:00",
                "adults": 3, "children": 1,
                "origin_country": "DE",
            },
        ]
        df = DataTransformer.extract_contextual_features(records)

        assert len(df) == 1  # both on 2026-03-01
        row = df.iloc[0]
        assert row["avg_los"] == pytest.approx((2.0 + 3.0) / 2)
        assert row["avg_party_size"] == pytest.approx((2.0 + 4.0) / 2)
        assert row["intl_guest_ratio"] == pytest.approx(0.5)
        assert row["arrival_time_score"] == pytest.approx((0.8 + 1.0) / 2)

    def test_records_missing_departure_default_to_los_one(self):
        records = [{
            "arrival": "2026-03-01T14:00:00",
            # no departure key
            "adults": 1, "children": 0,
            "origin_country": "FR",
        }]
        df = DataTransformer.extract_contextual_features(records)
        assert df.iloc[0]["avg_los"] == pytest.approx(1.0)


# ===========================================================================
# DataTransformer.merge_contextual_features
# ===========================================================================

class TestMergeContextualFeatures:

    def _make_prophet_df(self, dates=None):
        dates = dates or ["2026-03-01", "2026-03-02"]
        return pd.DataFrame({
            "ds": pd.to_datetime(dates),
            "y": list(range(50, 50 + len(dates))),
        })

    def test_merge_with_empty_contextual_fills_defaults(self):
        prophet_df = self._make_prophet_df()
        merged = DataTransformer.merge_contextual_features(prophet_df, pd.DataFrame())

        assert "avg_los" in merged.columns
        assert merged["avg_los"].iloc[0] == pytest.approx(2.0)
        assert merged["avg_party_size"].iloc[0] == pytest.approx(1.5)
        assert merged["intl_guest_ratio"].iloc[0] == pytest.approx(0.3)
        assert merged["arrival_time_score"].iloc[0] == pytest.approx(0.5)

    def test_merge_adds_contextual_columns_to_prophet_df(self):
        prophet_df = self._make_prophet_df(["2026-03-01"])
        ctx_df = pd.DataFrame({
            "ds": pd.to_datetime(["2026-03-01"]),
            "avg_los": [3.0],
            "avg_party_size": [2.5],
            "intl_guest_ratio": [0.4],
            "arrival_time_score": [0.9],
        })
        merged = DataTransformer.merge_contextual_features(prophet_df, ctx_df)

        row = merged.iloc[0]
        assert row["avg_los"] == pytest.approx(3.0)
        assert row["avg_party_size"] == pytest.approx(2.5)
        assert row["intl_guest_ratio"] == pytest.approx(0.4)
        assert row["arrival_time_score"] == pytest.approx(0.9)

    def test_merge_fills_defaults_for_missing_dates(self):
        """Dates not in contextual_df should receive neutral defaults."""
        prophet_df = self._make_prophet_df(["2026-03-01", "2026-03-02"])
        ctx_df = pd.DataFrame({
            "ds": pd.to_datetime(["2026-03-01"]),
            "avg_los": [3.0],
            "avg_party_size": [2.5],
            "intl_guest_ratio": [0.6],
            "arrival_time_score": [0.9],
        })
        merged = DataTransformer.merge_contextual_features(prophet_df, ctx_df)

        assert len(merged) == 2
        # 2026-03-02 should have defaults
        row2 = merged[merged["ds"] == pd.Timestamp("2026-03-02")].iloc[0]
        assert row2["avg_los"] == pytest.approx(2.0)
        assert row2["intl_guest_ratio"] == pytest.approx(0.3)


# ===========================================================================
# PredictionEngine.train — contextual regressor registration
# ===========================================================================

class TestPredictionEngineContextualRegressors:
    """Verify that the engine registers HOS-106 regressors when present."""

    def _make_training_df(self, include_contextual: bool = True):
        dates = pd.date_range("2026-01-01", periods=30, freq="D")
        df = pd.DataFrame({"ds": dates, "y": [40 + i for i in range(30)]})
        if include_contextual:
            df["avg_los"] = 2.0
            df["avg_party_size"] = 1.8
            df["intl_guest_ratio"] = 0.3
            df["arrival_time_score"] = 0.7
        return df

    def test_train_registers_contextual_regressors_when_present(self):
        from app.services.prediction_engine import PredictionEngine

        engine = PredictionEngine()
        df = self._make_training_df(include_contextual=True)
        engine.train(df, include_weather=False, include_events=False, include_occupancy=False)

        assert "avg_los" in engine.regressors
        assert "avg_party_size" in engine.regressors
        assert "intl_guest_ratio" in engine.regressors
        assert "arrival_time_score" in engine.regressors

    def test_train_skips_contextual_regressors_when_absent(self):
        from app.services.prediction_engine import PredictionEngine

        engine = PredictionEngine()
        df = self._make_training_df(include_contextual=False)
        engine.train(df, include_weather=False, include_events=False, include_occupancy=False)

        assert "avg_los" not in engine.regressors
        assert "arrival_time_score" not in engine.regressors

    def test_predict_passes_contextual_features_to_model(self):
        """After training with contextual regressors, predict() accepts them in features dict."""
        from datetime import date
        from app.services.prediction_engine import PredictionEngine

        engine = PredictionEngine()
        df = self._make_training_df(include_contextual=True)
        engine.train(df, include_weather=False, include_events=False, include_occupancy=False)

        features = {
            "avg_los": 3.0,
            "avg_party_size": 2.5,
            "intl_guest_ratio": 0.5,
            "arrival_time_score": 0.9,
        }
        result = engine.predict(date(2026, 4, 1), features=features)
        assert result.predicted >= 0
        assert 0.0 <= result.confidence <= 1.0
