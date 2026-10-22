"""AI Data Analysis Assistant - Streamlit app.  Run with:  streamlit run app.py"""
import os

import matplotlib.pyplot as plt
import streamlit as st

import ai
import analysis
import charts
import report

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "sample_data", "sales_sample.csv")

st.set_page_config(page_title="AI Data Analysis Assistant", page_icon="📊", layout="wide")


def show(fig):
    st.pyplot(fig)
    plt.close(fig)


# ---------------- sidebar ----------------
with st.sidebar:
    st.title("📊 Data Assistant")
    uploaded = st.file_uploader("Upload a CSV or Excel file", type=["csv", "xlsx", "xls"])
    use_sample = st.checkbox("Use the sample sales data", value=uploaded is None)
    api_key = st.text_input("Gemini API key (optional)", type="password",
                            value=os.getenv("GEMINI_API_KEY", ""),
                            help="Needed only for the AI tabs. Get a free key at aistudio.google.com/apikey")
    st.caption("Everything except the AI answers works without a key. "
               "The AI only receives a text summary of your data, not the whole file.")

# ---------------- load data ----------------
source_name, df = None, None
try:
    if uploaded is not None:
        source_name = uploaded.name
        df = analysis.load_file(uploaded, uploaded.name)
    elif use_sample:
        source_name = "sales_sample.csv"
        df = analysis.load_file(SAMPLE_PATH, source_name)
except Exception as exc:
    st.error(f"Could not read the file: {exc}")
    st.stop()

if df is None:
    st.title("AI Data Analysis Assistant")
    st.info("Upload a CSV or Excel file in the sidebar, or tick 'Use the sample sales data'.")
    st.stop()

# Keep the cleaned version in session so it survives button clicks.
if st.session_state.get("source") != source_name:
    st.session_state.source = source_name
    st.session_state.df = df
    st.session_state.chat = []
    st.session_state.ai_summary = None
    st.session_state.pdf = None

data = st.session_state.df
st.title("AI Data Analysis Assistant")
st.caption(f"Working on: **{source_name}**")

tab_overview, tab_quality, tab_charts, tab_ai, tab_report = st.tabs(
    ["Overview", "Data Quality", "Charts", "Ask AI", "PDF Report"])

# ---------------- overview ----------------
with tab_overview:
    info = analysis.overview(data)
    cols = st.columns(5)
    cols[0].metric("Rows", f"{info['rows']:,}")
    cols[1].metric("Columns", info["columns"])
    cols[2].metric("Missing cells", info["missing_cells"])
    cols[3].metric("Duplicate rows", info["duplicate_rows"])
    cols[4].metric("Quality score", f"{analysis.quality_score(data)}/100")

    st.subheader("Key insights")
    for note in analysis.insights(data):
        st.write("• " + note)

    st.subheader("Preview")
    st.dataframe(data.head(50))
    st.subheader("Columns")
    st.dataframe(analysis.column_summary(data))
    stats = analysis.numeric_stats(data)
    if not stats.empty:
        st.subheader("Numeric statistics")
        st.dataframe(stats)

# ---------------- data quality ----------------
with tab_quality:
    left, right = st.columns(2)
    with left:
        st.subheader("Missing values")
        missing = analysis.missing_report(data)
        if missing.empty:
            st.success("No missing values.")
        else:
            st.dataframe(missing)
            show(charts.missing_bar(data))
    with right:
        st.subheader("Duplicate rows")
        dups = analysis.duplicate_rows(data)
        if dups.empty:
            st.success("No duplicate rows.")
        else:
            st.warning(f"{len(dups)} duplicate rows")
            st.dataframe(dups)
        st.subheader("Outliers (IQR rule)")
        outliers = analysis.find_outliers(data)
        if outliers.empty:
            st.success("No outliers found.")
        else:
            st.dataframe(outliers)

    st.subheader("Clean the data")
    c1, c2, c3 = st.columns(3)
    drop_dups = c1.checkbox("Remove duplicate rows", value=True)
    num_fill = c2.selectbox("Missing numbers", ["none", "mean", "median", "zero"])
    txt_fill = c3.selectbox("Missing text", ["none", "mode", "unknown"])
    b1, b2 = st.columns(2)
    if b1.button("Apply cleaning"):
        st.session_state.df = analysis.clean_data(data, drop_dups, num_fill, txt_fill)
        st.session_state.ai_summary = None
        st.session_state.pdf = None
        st.rerun()
    if b2.button("Reset to original file"):
        st.session_state.df = df
        st.session_state.ai_summary = None
        st.session_state.pdf = None
        st.rerun()
    st.download_button("Download current data as CSV", analysis.to_csv_bytes(data),
                       file_name="cleaned_data.csv", mime="text/csv")

# ---------------- charts ----------------
with tab_charts:
    numeric, text, dates = analysis.column_types(data)
    kind = st.selectbox("Chart type", ["Histogram", "Box plot", "Top categories", "Scatter plot",
                                       "Correlation heatmap", "Monthly trend"])
    if kind == "Histogram" and numeric:
        col = st.selectbox("Column", numeric)
        show(charts.histogram(data, col, st.slider("Bins", 5, 60, 20)))
    elif kind == "Box plot" and numeric:
        show(charts.boxplot(data, st.selectbox("Column", numeric)))
    elif kind == "Top categories" and text:
        show(charts.top_categories_bar(data, st.selectbox("Column", text)))
    elif kind == "Scatter plot" and len(numeric) >= 2:
        x = st.selectbox("X axis", numeric)
        y = st.selectbox("Y axis", [c for c in numeric if c != x])
        show(charts.scatter(data, x, y))
    elif kind == "Correlation heatmap" and len(numeric) >= 2:
        show(charts.correlation_heatmap(data))
    elif kind == "Monthly trend" and dates and numeric:
        show(charts.time_trend(data, st.selectbox("Date column", dates), st.selectbox("Value", numeric)))
    else:
        st.info("This chart needs columns your data does not have (for example numeric or date columns).")

# ---------------- ask AI ----------------
with tab_ai:
    if not api_key:
        st.info("Paste your Gemini API key in the sidebar to use this tab.")
    context = analysis.build_context(data)

    if st.button("Generate AI summary", disabled=not api_key):
        with st.spinner("Asking Gemini..."):
            try:
                st.session_state.ai_summary = ai.summarize(context, api_key)
            except ai.AIError as exc:
                st.error(str(exc))
    if st.session_state.get("ai_summary"):
        st.markdown(st.session_state.ai_summary)

    st.subheader("Chat with your data")
    for role, text_msg in st.session_state.chat:
        with st.chat_message(role):
            st.markdown(text_msg)
    question = st.chat_input("Ask a question, e.g. Which region has the highest revenue?")
    if question:
        with st.chat_message("user"):
            st.markdown(question)
        try:
            with st.spinner("Thinking..."):
                answer = ai.ask(question, context, api_key, history=st.session_state.chat)
        except ai.AIError as exc:
            answer = f"⚠️ {exc}"
        st.session_state.chat.append(("user", question))
        st.session_state.chat.append(("assistant", answer))
        with st.chat_message("assistant"):
            st.markdown(answer)

# ---------------- report ----------------
with tab_report:
    st.write("Create a PDF with the overview, insights, data quality, statistics and charts.")
    if st.session_state.get("ai_summary"):
        st.caption("The AI summary you generated will be included.")
    if st.button("Build PDF report"):
        with st.spinner("Building the report..."):
            st.session_state.pdf = report.build_pdf(data, source_name, st.session_state.get("ai_summary"))
    if st.session_state.get("pdf"):
        st.download_button("Download PDF report", st.session_state.pdf,
                           file_name="data_report.pdf", mime="application/pdf")