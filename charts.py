"""Matplotlib charts. Every function returns a Figure (Streamlit shows it, the PDF report embeds it)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PRIMARY = "#4f8cff"


def histogram(df, col, bins=20):
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.hist(df[col].dropna(), bins=bins, color=PRIMARY, edgecolor="white")
    ax.set_title(f"Distribution of {col}")
    ax.set_xlabel(col)
    ax.set_ylabel("Count")
    fig.tight_layout()
    return fig


def boxplot(df, col):
    fig, ax = plt.subplots(figsize=(6, 3.0))
    ax.boxplot(df[col].dropna(), vert=False, patch_artist=True, boxprops={"facecolor": PRIMARY})
    ax.set_title(f"Box plot of {col} (dots are outliers)")
    ax.set_xlabel(col)
    fig.tight_layout()
    return fig


def top_categories_bar(df, col, top=10):
    counts = df[col].value_counts().head(top).sort_values()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.barh(counts.index.astype(str), counts.values, color=PRIMARY)
    ax.set_title(f"Top {len(counts)} values of {col}")
    ax.set_xlabel("Count")
    fig.tight_layout()
    return fig


def correlation_heatmap(df):
    corr = df.select_dtypes(include="number").corr()
    n = len(corr)
    fig, ax = plt.subplots(figsize=(max(5, 0.8 * n + 2), max(4, 0.7 * n + 1.5)))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(n), corr.columns, rotation=45, ha="right")
    ax.set_yticks(range(n), corr.columns)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(im, ax=ax, shrink=0.8)
    ax.set_title("Correlation between numeric columns")
    fig.tight_layout()
    return fig


def missing_bar(df):
    pct = (df.isna().mean() * 100)
    pct = pct[pct > 0].sort_values()
    fig, ax = plt.subplots(figsize=(6, max(2.5, 0.4 * len(pct) + 1)))
    ax.barh(pct.index.astype(str), pct.values, color="#ff5c6c")
    ax.set_title("Missing values by column (%)")
    ax.set_xlabel("% missing")
    fig.tight_layout()
    return fig


def scatter(df, x, y):
    data = df[[x, y]].dropna()
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.scatter(data[x], data[y], s=14, alpha=0.6, color=PRIMARY)
    ax.set_title(f"{y} vs {x}")
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    fig.tight_layout()
    return fig


def time_trend(df, date_col, value_col):
    data = df[[date_col, value_col]].dropna().sort_values(date_col)
    monthly = data.set_index(date_col)[value_col].resample("MS").sum()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.plot(monthly.index, monthly.values, marker="o", color=PRIMARY)
    ax.set_title(f"Monthly total of {value_col}")
    ax.set_ylabel(value_col)
    fig.autofmt_xdate()
    fig.tight_layout()
    return fig
