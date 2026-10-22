"""All the data analysis logic (no Streamlit here, so it is easy to test)."""
import io
import warnings

import numpy as np
import pandas as pd


# ---------- loading ----------
def load_file(file, filename):
    """Read a CSV or Excel file (path or uploaded file object) into a DataFrame."""
    name = filename.lower()
    if name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
    elif name.endswith(".csv"):
        try:
            df = pd.read_csv(file)
        except UnicodeDecodeError:
            if hasattr(file, "seek"):
                file.seek(0)
            df = pd.read_csv(file, encoding="latin-1")
    else:
        raise ValueError("Please upload a .csv, .xlsx or .xls file")
    if df.empty:
        raise ValueError("The file has no data rows")
    df.columns = [str(c).strip() for c in df.columns]
    return parse_dates(df)


def parse_dates(df):
    """Turn text columns that look like dates into real dates."""
    df = df.copy()
    for col in df.columns:
        if not (pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_string_dtype(df[col])):
            continue
        sample = df[col].dropna().astype(str).head(200)
        if sample.empty or not any(ch.isdigit() for ch in sample.iloc[0]):
            continue
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = pd.to_datetime(df[col], errors="coerce", format="mixed")
        if parsed.notna().sum() >= 0.8 * df[col].notna().sum() and df[col].notna().sum() > 0:
            df[col] = parsed
    return df


# ---------- overview ----------
def column_types(df):
    numeric = df.select_dtypes(include="number").columns.tolist()
    dates = df.select_dtypes(include=["datetime", "datetimetz"]).columns.tolist()
    text = [c for c in df.columns if c not in numeric and c not in dates]
    return numeric, text, dates


def overview(df):
    numeric, text, dates = column_types(df)
    return {
        "rows": len(df), "columns": df.shape[1],
        "numeric_columns": len(numeric), "text_columns": len(text), "date_columns": len(dates),
        "missing_cells": int(df.isna().sum().sum()),
        "duplicate_rows": int(df.duplicated().sum()),
        "memory_kb": round(df.memory_usage(deep=True).sum() / 1024, 1),
    }


def column_summary(df):
    rows = []
    for col in df.columns:
        series = df[col]
        non_null = series.dropna()
        rows.append({
            "column": col, "type": str(series.dtype), "non_null": int(series.notna().sum()),
            "missing": int(series.isna().sum()),
            "missing_%": round(series.isna().mean() * 100, 1),
            "unique": int(series.nunique()),
            "example": str(non_null.iloc[0]) if len(non_null) else "",
        })
    return pd.DataFrame(rows)


# ---------- data quality ----------
def missing_report(df):
    out = column_summary(df)[["column", "missing", "missing_%"]]
    return out[out["missing"] > 0].sort_values("missing", ascending=False).reset_index(drop=True)


def duplicate_rows(df):
    return df[df.duplicated(keep="first")]


def find_outliers(df):
    """IQR rule: values below Q1 - 1.5*IQR or above Q3 + 1.5*IQR."""
    rows = []
    for col in df.select_dtypes(include="number").columns:
        s = df[col].dropna()
        if len(s) < 4:
            continue
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        low, high = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        count = int(((s < low) | (s > high)).sum())
        if count:
            rows.append({"column": col, "outliers": count, "lower_limit": round(low, 2),
                         "upper_limit": round(high, 2)})
    return pd.DataFrame(rows, columns=["column", "outliers", "lower_limit", "upper_limit"])


def quality_score(df):
    """0-100. Loses 1.5 points per 1% missing cells and 2 points per 1% duplicate rows."""
    if df.empty:
        return 0.0
    missing_pct = df.isna().sum().sum() / df.size * 100
    dup_pct = df.duplicated().sum() / len(df) * 100
    return round(max(0.0, 100 - 1.5 * missing_pct - 2 * dup_pct), 1)


def clean_data(df, drop_duplicates=True, numeric_fill="none", text_fill="none"):
    """numeric_fill: none | mean | median | zero.  text_fill: none | mode | unknown."""
    out = df.copy()
    if drop_duplicates:
        out = out.drop_duplicates().reset_index(drop=True)
    for col in out.select_dtypes(include="number").columns:
        if out[col].isna().any():
            if numeric_fill == "mean":
                out[col] = out[col].fillna(out[col].mean())
            elif numeric_fill == "median":
                out[col] = out[col].fillna(out[col].median())
            elif numeric_fill == "zero":
                out[col] = out[col].fillna(0)
    numeric, text, _ = column_types(out)
    for col in text:
        if out[col].isna().any():
            if text_fill == "unknown":
                out[col] = out[col].fillna("Unknown")
            elif text_fill == "mode" and not out[col].mode().empty:
                out[col] = out[col].fillna(out[col].mode().iloc[0])
    return out


# ---------- statistics ----------
def numeric_stats(df):
    num = df.select_dtypes(include="number")
    if num.empty:
        return pd.DataFrame()
    stats = num.describe().T
    stats["median"] = num.median()
    stats["skew"] = num.skew()
    return stats.round(2).reset_index().rename(columns={"index": "column"})


def top_categories(df, col, top=10):
    counts = df[col].value_counts(dropna=False).head(top)
    return counts.rename_axis(col).reset_index(name="count")


def correlation_matrix(df):
    num = df.select_dtypes(include="number")
    return num.corr().round(2) if num.shape[1] >= 2 else pd.DataFrame()


def strong_correlations(df, threshold=0.7):
    corr = correlation_matrix(df)
    pairs = []
    cols = list(corr.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = corr.loc[a, b]
            if pd.notna(r) and abs(r) >= threshold:
                pairs.append((a, b, float(r)))
    return sorted(pairs, key=lambda p: -abs(p[2]))


# ---------- plain-English insights (work without AI) ----------
def insights(df):
    notes = []
    info = overview(df)
    notes.append(f"The dataset has {info['rows']:,} rows and {info['columns']} columns "
                 f"({info['numeric_columns']} numeric, {info['text_columns']} text, {info['date_columns']} date).")
    notes.append(f"Data quality score: {quality_score(df)}/100.")
    if info["duplicate_rows"]:
        notes.append(f"{info['duplicate_rows']} duplicate rows found. Consider removing them.")
    for _, row in missing_report(df).iterrows():
        level = "High" if row["missing_%"] >= 30 else "Some"
        notes.append(f"{level} missing values in '{row['column']}': {row['missing']} ({row['missing_%']}%).")
    for a, b, r in strong_correlations(df)[:5]:
        direction = "positively" if r > 0 else "negatively"
        notes.append(f"'{a}' and '{b}' are strongly {direction} correlated (r = {r:.2f}).")
    for _, row in find_outliers(df).iterrows():
        notes.append(f"'{row['column']}' has {row['outliers']} outlier value(s) outside "
                     f"{row['lower_limit']} to {row['upper_limit']}.")
    for col in df.columns:
        if df[col].nunique(dropna=True) == 1:
            notes.append(f"'{col}' has only one unique value, so it carries no information.")
    for col in df.select_dtypes(include="number").columns:
        skew = df[col].skew()
        if pd.notna(skew) and abs(skew) > 1.5:
            notes.append(f"'{col}' is heavily skewed (skew = {skew:.1f}); the mean may be misleading.")
    return notes


# ---------- text summary sent to the AI ----------
def build_context(df, max_columns=40, sample_rows=5):
    """A compact text description of the data. The AI only sees this, never the whole file."""
    d = df.iloc[:, :max_columns]
    info = overview(d)
    lines = [f"Rows: {info['rows']}, Columns: {info['columns']}, Missing cells: {info['missing_cells']}, "
             f"Duplicate rows: {info['duplicate_rows']}, Quality score: {quality_score(d)}/100",
             "", "COLUMNS (name | type | missing | unique):"]
    for _, r in column_summary(d).iterrows():
        lines.append(f"- {r['column']} | {r['type']} | {r['missing']} | {r['unique']}")
    stats = numeric_stats(d)
    if not stats.empty:
        lines += ["", "NUMERIC STATS:", stats.to_csv(index=False).strip()]
    _, text_cols, _ = column_types(d)
    for col in text_cols[:8]:
        if d[col].nunique() <= 30:
            top = d[col].value_counts().head(8)
            lines.append(f"Top values of {col}: " + ", ".join(f"{k} ({v})" for k, v in top.items()))
    pairs = strong_correlations(d)[:5]
    if pairs:
        lines += ["", "STRONG CORRELATIONS: " + "; ".join(f"{a} vs {b} = {r:.2f}" for a, b, r in pairs)]
    lines += ["", f"FIRST {sample_rows} ROWS:", d.head(sample_rows).to_csv(index=False).strip()]
    return "\n".join(lines)


def to_csv_bytes(df):
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
