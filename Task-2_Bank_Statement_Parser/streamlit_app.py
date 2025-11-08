import streamlit as st
import tempfile
import os
import json
import pandas as pd
from dotenv import load_dotenv
from bank_parser import process_bank_statement


st.set_page_config(page_title="Bank Statement Analyzer", page_icon="💼", layout="wide")

st.markdown("""
<style>
.stApp {
    background-color: #121212;
    color: #e0e0e0;
    font-family: 'Segoe UI', sans-serif;
}
h1 {
    color: #90caf9;
    font-size: 28px;
    margin-bottom: 8px;
}
h3 {
    color: #90caf9;
    font-size: 18px;
    margin: 15px 0 8px 0;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 0.5rem;
    max-width: 2000px;
}
.profile-card {
    background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    padding: 16px 20px;
    border-radius: 8px;
    margin-bottom: 15px;
    box-shadow: 0 3px 5px rgba(0, 0, 0, 0.3);
}
.profile-header {
    display: flex;
    align-items: flex-start;
    margin-bottom: 12px;
}
.profile-icon {
    font-size: 36px;
    margin-right: 15px;
    flex-shrink: 0;
    line-height: 1;
}
.profile-info {
    flex: 1;
}
.profile-info h2 {
    margin: 0 0 8px 0;
    color: #ffffff;
    font-size: 19px;
    line-height: 1.2;
}
.profile-info p {
    margin: 0 0 4px 0;
    color: #b3d9ff;
    font-size: 12px;
    line-height: 1.5;
}
.profile-stats {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-top: 8px;
}
.stat-box {
    background-color: rgba(255, 255, 255, 0.1);
    padding: 8px;
    border-radius: 5px;
    text-align: center;
}
.stat-label {
    color: #b3d9ff;
    font-size: 10px;
    margin-bottom: 2px;
}
.stat-value {
    color: #ffffff;
    font-size: 15px;
    font-weight: bold;
}
div[data-testid="stFileUploader"] {
    margin-bottom: 12px;
}
div[data-testid="stExpander"] {
    margin-top: 8px;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("❌ GEMINI_API_KEY not found. Please check your .env file.")
    st.stop()

col1, col2 = st.columns([5, 1])
with col1:
    st.title("💳 Bank Statement Analyzer")
with col2:
    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
    test_mode = st.checkbox("Test Mode", False)

uploaded_file = st.file_uploader("Upload your bank statement", type=["pdf", "png", "jpg", "jpeg"], label_visibility="collapsed")

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

    if "error" in result:
        st.error(result["error"])
    else:
        fields_outer = result.get("fields", {})
        fields = fields_outer.get("fields", {}) or fields_outer
        summary = fields_outer.get("summary", {})
        insights = result.get("insights", [])
        quality = result.get("quality", {})
        warnings = quality.get("warnings", [])

        # 2-Column Layout
        left_col, right_col = st.columns([1.5, 1])
        
        with left_col:
            # Profile Card
            st.markdown(f"""
            <div class='profile-card'>
                <div class='profile-header'>
                    <div class='profile-icon'>🏦</div>
                    <div class='profile-info'>
                        <h2>{fields.get('account_holder_name', 'N/A')}</h2>
                        <p>{fields.get('bank_name', 'N/A')} | {fields.get('account_type', 'N/A')} | Account: {fields.get('account_number_masked', '****')}</p>
                        <p>Statement Period: {fields.get('statement_month', 'N/A')} | Currency: {fields.get('currency', 'INR')}</p>
                    </div>
                </div>
                <div class='profile-stats'>
                    <div class='stat-box'>
                        <div class='stat-label'>Opening Balance</div>
                        <div class='stat-value'>{summary.get("opening_balance", "N/A")}</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-label'>Closing Balance</div>
                        <div class='stat-value'>{summary.get("closing_balance", "N/A")}</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-label'>Total Credits</div>
                        <div class='stat-value'>{summary.get("total_credits", "N/A")}</div>
                    </div>
                    <div class='stat-box'>
                        <div class='stat-label'>Total Debits</div>
                        <div class='stat-value'>{summary.get("total_debits", "N/A")}</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Transactions Table
            transactions = fields.get('transactions', []) or fields_outer.get('transactions', [])
            if transactions:
                st.markdown("### 📋 Transactions")
                trans_df = pd.DataFrame(transactions)
                table_height = min(38 + (len(trans_df) * 35) + 10, 400)
                st.dataframe(trans_df, use_container_width=True, height=table_height, hide_index=True)
            
            # Financial Insights
            if insights:
                st.markdown("### 💡 Financial Insights")
                for insight in insights:
                    st.markdown(f"• {insight}")
            
            # Warnings
            if warnings:
                with st.expander("⚠️ Warnings"):
                    for warn in warnings:
                        st.warning(warn)
        
        with right_col:
            # JSON Output
            st.markdown("### 🧾 JSON Output")
            st.json(result)