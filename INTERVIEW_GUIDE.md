# AI Data Analysis Assistant - Interview Guide

## 30-second pitch
"I built a data analysis web app with Python, Pandas and Streamlit. You upload a CSV or Excel file and it
shows statistics, finds missing values, duplicates and outliers, lets you clean the data, draws charts and
creates a PDF report. I also connected the Gemini API so you can ask questions in plain English.
I only send the AI a short text summary of the data, not the file, which is better for privacy and cost.
I wrote 18 automated tests for it."

## How it works
File -> `analysis.load_file` (Pandas) -> checks and statistics -> Streamlit shows tables and charts ->
`build_context` makes a short text summary -> `ai.ask` sends summary + question to Gemini -> answer shown in chat.

## Questions you may get
**How do you find outliers?** IQR rule: values below Q1 - 1.5xIQR or above Q3 + 1.5xIQR.

**How do you handle missing values?** Remove rows, or fill: mean/median for numbers (median is safer with outliers), most common value or "Unknown" for text.

**Why not send the whole file to the AI?** Large files are slow and costly, and may contain private data. A summary is enough for most questions.

**What if the AI makes up numbers?** The prompt tells it to answer only from the summary and say when it cannot. For exact numbers, the app's own tables are the source of truth.

**What is correlation?** How strongly two numeric columns move together, from -1 to 1. It does not prove one causes the other.

**How did you test it?** Unit tests on the analysis functions with small hand-made tables, a fake AI client so tests do not need a real key, and a test that the PDF is created.

**What would you improve?** Rebuild as React + FastAPI, add login, support large files, add more chart types, cache AI answers.

## Pandas lines to be able to explain
```python
df.isna().sum()          # missing values per column
df.duplicated().sum()    # number of duplicate rows
df.describe()            # count, mean, std, min, quartiles, max
df.corr(numeric_only=True)
df["col"].fillna(df["col"].median())
```
