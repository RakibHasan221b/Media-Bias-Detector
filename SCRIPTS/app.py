import os

import streamlit as st
from datetime import datetime

# Streamlit Cloud exposes secrets via st.secrets, not as OS env vars like a local
# .env file does. Bridge it here, before importing anything that reads the key
# via os.getenv() (llm.py). Locally, st.secrets is just empty/missing and this
# no-ops, falling back to llm.py's own load_dotenv() from .env as before.
if "OPENAI_API_KEY" not in os.environ:
    try:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass

from analysis import run_temporal_analysis
from llm import BiasEvaluator
from smart_system import run_analysis


TOPICS = ["All", "Russia Ukraine war", "Iran Israel war", "Taiwan strait conflict"]


st.title("News Bias Analysis System")
st.write("Compare BD vs International media + temporal changes")

analysis_mode = st.radio(
    "Select Analysis Mode",
    [
        "Current Bias Comparison (BD vs International)",
        "Temporal Change Analysis (Recent vs Past)",
    ],
    horizontal=True,
)


if analysis_mode == "Current Bias Comparison (BD vs International)":
    st.markdown("### Current Bias Comparison Parameters")

    keyword = st.text_input(
        "Keyword (optional)",
        placeholder="e.g. Russia, Ukraine, Hormuz, ceasefire",
    )

    topic = st.selectbox("Select Topic (optional)", TOPICS)

    start_date = st.date_input("Start Date", value=datetime(2026, 4, 11))
    end_date = st.date_input("End Date", value=datetime(2026, 4, 13))

    if start_date > end_date:
        st.error("Start date cannot be after end date")
        st.stop()

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
                end_date=end_str,
            )

            if isinstance(result, tuple) and len(result) == 3:
                st.session_state.analysis_result = result[0]
                st.session_state.bd_texts = result[1]
                st.session_state.intl_texts = result[2]
            else:
                st.session_state.analysis_result = result
                st.session_state.bd_texts = None
                st.session_state.intl_texts = None

        st.session_state.eval_result = None

    if st.session_state.analysis_result:
        st.subheader("Bias Analysis Result")
        st.markdown(st.session_state.analysis_result)

        show_eval = st.checkbox(
            "Run Detailed Evaluation (uses GPT-4o)",
            help="Evaluate the quality, fidelity, and balance of the generated analysis against the original articles.",
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
                            end_date=end_date.strftime("%Y-%m-%d"),
                        )

            if st.session_state.eval_result:
                st.subheader("Academic Evaluation")
                st.markdown(st.session_state.eval_result)
    else:
        st.info("Run an analysis to see results and evaluation options.")

else:
    st.markdown("### Temporal Change Analysis")

    temporal_topic = st.selectbox("Select Topic", TOPICS[1:], key="temporal_topic")

    time_period = st.selectbox(
        "Compare recent articles with articles from",
        ["7 days ago", "1 month ago", "3 months ago", "6 months ago"],
    )

    st.info(
        f"Will compare recent articles from the last 10 days with articles from {time_period} "
        "for BBC, The Guardian, The Daily Star, and New Age."
    )

    if "temporal_global" not in st.session_state:
        st.session_state.temporal_global = None
    if "temporal_per_paper" not in st.session_state:
        st.session_state.temporal_per_paper = {}
    if "temporal_metadata" not in st.session_state:
        st.session_state.temporal_metadata = {}

    if st.button("Run Temporal Analysis", type="primary"):
        with st.spinner(f"Fetching articles and analyzing changes over {time_period}..."):
            global_analysis, per_paper, metadata = run_temporal_analysis(
                temporal_topic,
                time_period,
            )

            st.session_state.temporal_global = global_analysis
            st.session_state.temporal_per_paper = per_paper
            st.session_state.temporal_metadata = metadata

    if st.session_state.temporal_global:
        metadata = st.session_state.temporal_metadata

        st.subheader(f"Temporal Analysis - {temporal_topic} ({time_period})")

        if metadata:
            st.caption(
                f"Recent: {metadata['recent_start']} to {metadata['recent_end']} | "
                f"Past: {metadata['old_start']} to {metadata['old_end']}"
            )

        st.markdown(st.session_state.temporal_global)

        st.subheader("Per Newspaper Changes")
        for paper, analysis in st.session_state.temporal_per_paper.items():
            with st.expander(paper):
                st.markdown(analysis)