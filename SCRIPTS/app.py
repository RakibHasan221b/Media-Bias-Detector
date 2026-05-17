import streamlit as st
from datetime import datetime
from smart_system import run_analysis  # your existing function
# Import the evaluator (adjust path if needed)
from llm import BiasEvaluator, BiasEngine  # or wherever your classes are

st.title("News Bias Analysis System")
st.write("Compare BD vs International media narratives")

st.markdown("### Select Analysis Parameters")

keyword = st.text_input(
    "Keyword (optional)",
    placeholder="e.g. Russia, Ukraine, Hormuz, ceasefire"
)

topic = st.selectbox(
    "Select Topic (optional)",
    ["All", "Russia Ukraine war", "Iran Israel war", "Taiwan strait conflict"]
)

start_date = st.date_input("Start Date", value=datetime(2026, 4, 11))
end_date = st.date_input("End Date", value=datetime(2026, 4, 13))

if start_date > end_date:
    st.error("Start date cannot be after end date")
    st.stop()

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "bd_texts" not in st.session_state:
    st.session_state.bd_texts = None
if "intl_texts" not in st.session_state:
    st.session_state.intl_texts = None
if "eval_result" not in st.session_state:
    st.session_state.eval_result = None

if st.button("Run Analysis", type="primary"):
    with st.spinner("Analyzing news and detecting bias..."):
        start_str = start_date.strftime("%Y-%m-%d")
        end_str = end_date.strftime("%Y-%m-%d")

        result = run_analysis(
            keyword=keyword.strip() if keyword and keyword.strip() else None,
            topic=topic if topic != "All" else None,
            start_date=start_str,
            end_date=end_str
        )

        # Assuming run_analysis now returns a tuple: (analysis_text, bd_texts, intl_texts)
        if isinstance(result, tuple) and len(result) == 3:
            st.session_state.analysis_result = result[0]
            st.session_state.bd_texts = result[1]
            st.session_state.intl_texts = result[2]
        else:
            st.session_state.analysis_result = result
            # If you can't change run_analysis yet, you may need to fetch texts separately

    # Clear previous evaluation when new analysis runs
    st.session_state.eval_result = None

# ==================== DISPLAY ANALYSIS ====================
if st.session_state.analysis_result:
    st.subheader("Bias Analysis Result")
    st.markdown(st.session_state.analysis_result)

    # ==================== EVALUATION CHECKBOX ====================
    show_eval = st.checkbox(
        "Run Detailed Evaluation (uses GPT-4o)",
        help="This will evaluate the quality, fidelity, and balance of the generated analysis against the original articles."
    )

    if show_eval:
        if st.session_state.eval_result is None:
            if st.session_state.bd_texts is None or st.session_state.intl_texts is None:
                st.warning("Original articles not available for evaluation.")
            else:
                with st.spinner("Running academic evaluation with GPT-4o..."):
                    evaluator = BiasEvaluator()
                    st.session_state.eval_result = evaluator.evaluate(
                        analysis_text=st.session_state.analysis_result,
                        bd_texts=st.session_state.bd_texts,
                        intl_texts=st.session_state.intl_texts,
                        topic=topic if topic != "All" else "General",
                        start_date=start_date.strftime("%Y-%m-%d"),
                        end_date=end_date.strftime("%Y-%m-%d")
                    )

        if st.session_state.eval_result:
            st.subheader("📊 Academic Evaluation")
            st.markdown(st.session_state.eval_result)
else:
    st.info("Run an analysis to see results and evaluation options.")