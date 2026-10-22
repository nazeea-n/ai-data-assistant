import numpy as np
import pandas as pd

import analysis


def make_df():
    return pd.DataFrame({
        "id": [1, 2, 3, 4, 5, 6, 7, 8, 9, 9],
        "price": [10.0, 12.0, np.nan, 11.0, 13.0, 12.0, 11.0, 10.0, 500.0, 500.0],
        "city": ["A", "B", "A", None, "B", "A", "B", "A", "B", "B"],
        "constant": [1] * 10,
    })


def test_overview_counts():
    info = analysis.overview(make_df())
    assert info["rows"] == 10 and info["columns"] == 4
    assert info["missing_cells"] == 2 and info["duplicate_rows"] == 1


def test_missing_report_lists_only_columns_with_gaps():
    report = analysis.missing_report(make_df())
    assert set(report["column"]) == {"price", "city"}


def test_find_outliers_detects_extreme_value():
    out = analysis.find_outliers(make_df())
    assert "price" in out["column"].values


def test_quality_score_perfect_and_penalised():
    clean = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    assert analysis.quality_score(clean) == 100.0
    assert analysis.quality_score(make_df()) < 100.0


def test_clean_data_drops_duplicates_and_fills():
    cleaned = analysis.clean_data(make_df(), True, "median", "unknown")
    assert len(cleaned) == 9
    assert cleaned["price"].isna().sum() == 0
    assert "Unknown" in cleaned["city"].values


def test_clean_data_without_options_changes_nothing_but_duplicates():
    cleaned = analysis.clean_data(make_df(), False, "none", "none")
    assert cleaned.equals(make_df())


def test_strong_correlations_found():
    df = pd.DataFrame({"x": range(20), "y": [v * 2 for v in range(20)], "z": [5, 1] * 10})
    pairs = analysis.strong_correlations(df)
    assert pairs and pairs[0][:2] == ("x", "y")


def test_insights_mention_problems():
    text = " ".join(analysis.insights(make_df()))
    assert "duplicate" in text and "missing" in text and "outlier" in text and "one unique value" in text


def test_build_context_contains_key_parts():
    ctx = analysis.build_context(make_df())
    assert "Rows: 10" in ctx and "price" in ctx and "FIRST 5 ROWS" in ctx


def test_load_csv_and_date_detection(tmp_path):
    path = tmp_path / "d.csv"
    path.write_text("when,amount\n2025-01-05,10\n2025-02-10,20\n2025-03-15,30\n")
    df = analysis.load_file(str(path), "d.csv")
    assert str(df["when"].dtype).startswith("datetime")


def test_load_rejects_wrong_type():
    try:
        analysis.load_file("x.txt", "x.txt")
        assert False, "should have raised"
    except ValueError as exc:
        assert "csv" in str(exc).lower()


def test_sample_file_has_planted_problems():
    df = analysis.load_file("sample_data/sales_sample.csv", "sales_sample.csv")
    info = analysis.overview(df)
    assert info["duplicate_rows"] == 5 and info["missing_cells"] > 0
    assert "revenue" in analysis.find_outliers(df)["column"].values
