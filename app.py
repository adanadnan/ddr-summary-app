import streamlit as st
import requests
import time
import json
from datetime import datetime

# === CONFIGURATION ===
endpoint = "https://<your-resource-name>.cognitiveservices.azure.com/"
key = "<your-api-key>"
model_id = "DDR_Sample"
api_version = "2023-07-31"

# === STREAMLIT PAGE SETUP ===
st.set_page_config(page_title="DDR AI Summary", layout="centered")
st.title("📄 AI-Powered DDR Summary")
st.caption("Upload a Daily Drilling Report (PDF) and get instant, role-based summaries using Azure AI.")

uploaded_file = st.file_uploader("Upload DDR PDF", type=["pdf"])
show_raw = st.toggle("Show raw extracted fields")

if uploaded_file:
    st.info("⏳ Processing file. Please wait...")
    file_name = uploaded_file.name

    url = f"{endpoint}formrecognizer/documentModels/{model_id}:analyze?api-version={api_version}"
    headers = {
        "Content-Type": "application/pdf",
        "Ocp-Apim-Subscription-Key": key
    }

    response = requests.post(url, headers=headers, data=uploaded_file.read())

    if response.status_code != 202:
        st.error(f"❌ Submission failed: {response.status_code}")
    else:
        result_url = response.headers["Operation-Location"]
        with st.spinner("Analyzing document..."):
            while True:
                result_response = requests.get(result_url, headers={"Ocp-Apim-Subscription-Key": key})
                result_json = result_response.json()
                if result_json["status"] == "succeeded":
                    break
                elif result_json["status"] == "failed":
                    st.error("❌ Analysis failed.")
                    st.stop()
                time.sleep(1)

        try:
            document = result_json["analyzeResult"]["documents"][0]["fields"]
        except Exception:
            st.error("❌ No fields found in the extracted result.")
            st.stop()

        def safe(field):
            return document[field].get("content", "Not found") if field in document else "Not found"

        well_name = safe("WellName")
        report_date = safe("ReportDate")
        depth = safe("CurrentDepth")
        mud_weight = safe("MudWeight")
        drilling_hours = safe("DrillingHours")
        operation = safe("OperationType")
        remarks = safe("Remarks")

        def clean_remarks(text, max_chars=400):
            return text if len(text) <= max_chars else text[:max_chars].rsplit(".", 1)[0] + "..."

        short_remarks = clean_remarks(remarks)

        st.markdown("---")
        st.markdown(f"**🧾 File:** `{file_name}`")
        st.markdown(f"**🛢️ Well:** `{well_name}`")
        st.markdown(f"**📅 Report Date:** `{report_date}`")
        st.markdown(f"**🕒 Analyzed:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")

        st.markdown("---")
        st.subheader("🛠 Engineer Summary")
        st.success(f"Drilling ongoing at **{depth}**. Mud weight: **{mud_weight}**. No major issues. Operation: **{operation}**.")

        st.subheader("👷 Supervisor Summary")
        st.info(f"On **{report_date}** at **{well_name}**, operation included: **{operation}**.")
        st.markdown("**Summary:**")
        with st.expander("Show remarks"):
            st.write(remarks)

        st.subheader("📊 Analyst Summary")
        st.warning(f"Drilling time: **{drilling_hours} hrs**. Mud weight: **{mud_weight}**.")
        st.markdown("**Key remarks:**")
        st.write(short_remarks)

        if show_raw:
            st.markdown("---")
            st.subheader("🧾 Raw Extracted Fields")
            st.json({k: v.get("content", "Not found") for k, v in document.items()})