import os
import requests
import streamlit as st
from dotenv import load_dotenv
load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Business Intelligence Assistant", page_icon="📊", layout="wide")
st.title("📊 AI Business Intelligence Assistant")
st.caption("Ask questions about the supplied sales transactions in plain English.")

with st.sidebar:
    st.subheader("Try these questions")
    examples = [
        "What is the total revenue?",
        "Which product generated the highest revenue?",
        "Show the monthly revenue trend",
        "Which region generated the highest sales?",
        "Compare January and February revenue"
    ]
    for example in examples:
        if st.button(example, use_container_width=True):
            st.session_state["question"] = example
    st.divider()
    st.caption("Revenue = quantity × unit price − discount. Only valid completed transactions are included.")

question = st.text_input("Ask a sales question", key="question", placeholder="e.g. Which region generated the highest sales?")
if st.button("Analyze", type="primary") and question.strip():
    try:
        with st.spinner("Analyzing sales data..."):
            response = requests.post(f"{API_URL}/ask", json={"question": question}, timeout=60)
        if response.ok:
            result = response.json()
            st.subheader(result["title"])
            st.success(result["answer"])
            st.caption(f"Question interpretation: {result.get('question_interpreter', 'Not specified')}")
            st.write("**Supporting figures**")
            data = result.get("supporting_data", {})
            if "monthly_revenue" in data:
                st.dataframe(data["monthly_revenue"], use_container_width=True)
                if data["monthly_revenue"]:
                    st.bar_chart({r["month"]: r["revenue"] for r in data["monthly_revenue"]})
            elif "product_revenue" in data:
                st.dataframe(data["product_revenue"], use_container_width=True)
            elif "region_revenue" in data:
                st.dataframe(data["region_revenue"], use_container_width=True)
            else:
                st.json(data)
            with st.expander("How was this calculated?"):
                st.write(result.get("calculation"))
        else:
            st.error(response.json().get("detail", "The request could not be processed."))
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to the backend. Start the FastAPI server first.")
    except requests.exceptions.Timeout:
        st.error("The request timed out. Please try again.")
    except Exception as exc:
        st.error(f"Unexpected error: {exc}")
elif st.button("Check backend"):
    try:
        r = requests.get(f"{API_URL}/health", timeout=5)
        st.info("Backend is running." if r.ok else "Backend health check failed.")
    except requests.exceptions.RequestException:
        st.error("Backend is not reachable.")
