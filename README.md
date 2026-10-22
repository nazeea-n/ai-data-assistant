# AI Data Analysis Assistant

Upload a CSV or Excel file and get instant statistics, data-quality checks, charts, a PDF report,
and a chat where you can ask questions about your data in plain English (powered by Google Gemini).

**Tech:** Python, Pandas, NumPy, Matplotlib, Streamlit, Google Gemini API, ReportLab, pytest

## Features
- Upload CSV / Excel (or use the built-in sample sales data)
- Overview: rows, columns, types, statistics, and an auto-written list of key insights
- Data quality: missing values, duplicate rows, outliers (IQR rule), 0-100 quality score
- One-click cleaning: remove duplicates, fill missing numbers (mean / median / zero) and text (mode / "Unknown")
- Charts: histogram, box plot, top categories, scatter, correlation heatmap, monthly trend
- Ask AI: summary and chat. The AI only gets a short text summary of the data, never the whole file
- PDF report download
- 18 automated tests

---

## Setup on Windows (do these steps in order)

**Step 1.** Unzip the folder, open it in VS Code (File > Open Folder > `ai-data-assistant`).

**Step 2.** Open the terminal (Terminal > New Terminal) and paste:
```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3.** Run the app:
```
streamlit run app.py
```
Your browser opens at http://localhost:8501. Everything works now **except the AI tab**.

**Step 4 (for the AI tab).** Get a free key at https://aistudio.google.com/apikey, then either
- paste it into the sidebar box in the app, or
- run `copy .env.example .env`, open `.env`, and replace `your_key_here` with your key.

If you get a "model not found" error, open `.env` and change `GEMINI_MODEL` to a current model name
shown in Google AI Studio.

## Try it in 2 minutes
1. Keep "Use the sample sales data" ticked. Look at **Overview** > Key insights.
2. Open **Data Quality**. The sample has planted problems: 5 duplicate rows, missing values, 2 huge revenue outliers.
3. Choose "Remove duplicate rows" + "median" + "Unknown" > **Apply cleaning**. Watch the quality score go up.
4. Open **Charts**, then **PDF Report** > Build > Download.
5. With a key: **Ask AI** > "Which category earns the most revenue?"

## Run the tests
```
pytest
```

## Project structure
| File | What it does |
|---|---|
| `app.py` | The Streamlit screens |
| `analysis.py` | Loading, statistics, quality checks, cleaning, insights |
| `charts.py` | Matplotlib charts |
| `ai.py` | Gemini questions and prompt building |
| `report.py` | PDF report with ReportLab |
| `sample_data/` | Practice file with planted problems |
| `tests/` | pytest tests |

## How the quality score works
`100 - 1.5 x (% missing cells) - 2 x (% duplicate rows)`, never below 0.
