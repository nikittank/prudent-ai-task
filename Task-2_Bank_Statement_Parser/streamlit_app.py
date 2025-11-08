import streamlit as st
import tempfile
import os
import json
from dotenv import load_dotenv
from bank_parser import process_bank_statement


st.set_page_config(page_title="💳 Bank Statement Analyzer", page_icon="💼", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
h1, h2, h3, h4 {
    color: #90caf9;
}
hr {
    border: 1px solid #1f2937;
    margin: 1rem 0;
}
.insight-box {
    background-color: #1e1e1e;
    padding: 8px 12px;
    border-radius: 6px;
    margin-bottom: 5px;
}
.stExpander {
    background-color: #1e1e1e !important;
}
div[data-testid="stMetricValue"] {
    color: #ffffff;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY not found. Please check your .env file.")
    st.stop()
else:
    st.sidebar.success("✅ Gemini API Key Loaded")

with st.sidebar:
    st.header("⚙️ Settings")
    test_mode = st.toggle("Run in Test Mode", False)

st.title("💳 Bank Statement Analyzer")
st.write("Upload your **bank statement (PDF or Image)** to extract and summarize details.")

uploaded_file = st.file_uploader("Upload File", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    with st.spinner("⏳ Processing your bank statement... Please wait."):
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp:
                tmp.write(uploaded_file.read())
                file_path = tmp.name

            # Process file
            result = process_bank_statement(file_path, test_mode=test_mode)

        except Exception as e:
            st.error(f"❌ Processing failed: {e}")
            st.stop()

    # Once done, remove spinner and show results
    if "error" in result:
        st.error(result["error"])
    else:
        fields_outer = result.get("fields", {})
        fields = fields_outer.get("fields", {}) or fields_outer
        summary = fields_outer.get("summary", {})
        insights = result.get("insights", [])
        quality = result.get("quality", {})

        # 🏦 Account Information
        st.subheader("🏦 Account Information")
        col1, col2, col3 = st.columns(3)
        with col1: st.markdown(f"**Bank:** {fields.get('bank_name', 'N/A')}")
        with col2: st.markdown(f"**Holder:** {fields.get('account_holder_name', 'N/A')}")
        with col3: st.markdown(f"**Account:** {fields.get('account_number_masked', '****')}")

        col4, col5, col6 = st.columns(3)
        with col4: st.markdown(f"**Type:** {fields.get('account_type', 'N/A')}")
        with col5: st.markdown(f"**Currency:** {fields.get('currency', 'INR')}")
        with col6: st.markdown(f"**Month:** {fields.get('statement_month', 'N/A')}")

        st.markdown("<hr>", unsafe_allow_html=True)

        # 💰 Account Summary
        st.subheader("💰 Account Summary")
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Opening", summary.get("opening_balance", "N/A"))
        with col2: st.metric("Closing", summary.get("closing_balance", "N/A"))
        with col3: st.metric("Credits", summary.get("total_credits", "N/A"))
        with col4: st.metric("Debits", summary.get("total_debits", "N/A"))
        if summary.get("average_daily_balance"):
            st.metric("Average Daily Balance", summary["average_daily_balance"])

        st.markdown("<hr>", unsafe_allow_html=True)

        # 💡 Financial Insights
        st.subheader("💡 Financial Insights")
        if insights:
            for insight in insights:
                st.markdown(f"<div class='insight-box'>• {insight}</div>", unsafe_allow_html=True)
        else:
            st.info("No insights generated.")

        # ⚠️ Warnings
        warnings = quality.get("warnings", [])
        if warnings:
            st.markdown("<hr>", unsafe_allow_html=True)
            st.subheader("⚠️ Warnings")
            for warn in warnings:
                st.warning(warn)

        # 🧾 JSON Output — Structured
        st.markdown("<hr>", unsafe_allow_html=True)
        st.subheader("🧾 JSON Summary")

        with st.expander("Click to View Structured JSON", expanded=False):
            st.json(result)
