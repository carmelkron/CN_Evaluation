import streamlit as st
import pandas as pd
import numpy as np
import time
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# Set up the page
st.set_page_config(layout="wide")

# Initialize session state with the dataset connection and the dataset itself
if 'dataset_conn' not in st.session_state:
    st.session_state.dataset_conn = st.connection('dataset', type=GSheetsConnection)
    st.session_state.dataset_df = pd.DataFrame(st.session_state.dataset_conn.read(worksheet="cn_dataset_styles", ttl=1))
    st.session_state.last_response_id = None
    st.session_state.selection = None
    st.session_state.start_time = None

# Mapping log-in data (mail address) to the evaluator id's
mapping = {
    'bethany.meidinger@gmail.com' : 1,
    'daikimai@fuji.waseda.jp' : 2,
    'linahutchinson@ruri.waseda.jp': 3,
    'lilymcree@gmail.com': 4,
    'yijing_at_waseda@moegi.waseda.jp': 5
}

# KPIs
kpis = {
    1: "Which do you find more convincing as a rebuttal to the opinion displayed above, A or B?",
    2: "Which evokes stronger emotions, A or B?",
    3: "Which do you think the average social media user is more likely to find interesting to share (repost/retweet), A or B?"
}

# Login Form
def login():
    st.markdown("""
        <style>
        .main {
            max-width: 1000px;
            margin: 0 auto;
            padding-top: 50px;
        }
        </style>
        """, unsafe_allow_html=True)
    st.title("Please enter your mail address")
    email = st.text_input(" ", placeholder="mail address")
    st.markdown(" ")
    if st.button("Log in"):
        eval_id = mapping.get(email, 0)
        if eval_id == 0:
            st.error("Please check again the mail address you entered.")
        else:
            st.session_state.eval_id = eval_id
            st.session_state.eval_connection = st.connection(f"eval_{eval_id}", type=GSheetsConnection)
            st.session_state.eval_comparisons = pd.DataFrame(st.session_state.eval_connection.read(worksheet="comparisons", ttl=1))
            last_response_id = pd.DataFrame(st.session_state.eval_connection.read(worksheet="evaluations", ttl=1))['response_id'].max()
            st.write(last_response_id)
            if last_response_id is np.nan:
                st.session_state.last_response_id = 0
            else:
                st.session_state.last_response_id = int(last_response_id)
            st.rerun()

# Main app
def main():
    if st.session_state.start_time is None:
        st.session_state.start_time = time.perf_counter()
    # Data of the current comparison tbd
    curr_comparison = st.session_state.eval_comparisons.iloc[st.session_state.last_response_id]
    base_claim_id = int(curr_comparison['base_claim_id'])
    left_narrative_id = int(curr_comparison['left_narrative_id'])
    right_narrative_id = int(curr_comparison['right_narrative_id'])
    kpi_id = int(curr_comparison['kpi_id'])

    # Data from the dataset regarding the current comparison
    base_claim = st.session_state.dataset_df[st.session_state.dataset_df["base_claim_id"] == base_claim_id]["base_claim"][0]
    kpi = kpis[kpi_id]
    left_cn = st.session_state.dataset_df[st.session_state.dataset_df["narrative_id"] == left_narrative_id]["narrative_text"].values[0]
    right_cn = st.session_state.dataset_df[st.session_state.dataset_df["narrative_id"] == right_narrative_id]["narrative_text"].values[0]
    st.markdown("""
    <style>
        body {
            overflow-y: scroll;
        }
        .main {
            padding-left: 5%;
            padding-right: 5%;
        }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.last_response_id > 3060:
        st.markdown("<h1 style='text-align: center;'>You finished you evaluations! Thank you for your effort!</h1>", unsafe_allow_html=True)
        return
    
    st.markdown(f"<h4 style='text-align:center;'>Look at this claim</h4>", unsafe_allow_html=True)
    st.markdown(f'<p style="color:red; text-align:center; font-size: 30px;">{base_claim}</p>', unsafe_allow_html=True)
    
    st.markdown(f'<h4 style="text-align:center; max-width: 60%; margin: 0 auto;">{kpi}</h4>', unsafe_allow_html=True)
    
    col1, col_middle, col2 = st.columns([15,1,15])
    st.markdown("""
    <style>                    
    .equal-height-paragraph {
        padding: 10px;
        text-align: center;
        font-size: 25px; 
        border: 2px solid black;
        display: flex;
        flex-direction: column;
        justify-content: center;
        width: fit-content;
        height: 300px;
    }
    """, unsafe_allow_html=True)

    with col1:
        st.markdown("<h2 style='text-align:center;'>A</h2>", unsafe_allow_html=True)
        st.markdown(f'<p class="equal-height-paragraph">{left_cn}</p>', unsafe_allow_html=True)
        
    with col2:
        st.markdown("<h2 style='text-align:center;'>B</h2>", unsafe_allow_html=True)
        st.markdown(f'<p class="equal-height-paragraph">{right_cn}</p>', unsafe_allow_html=True)
        
    col1, col2, col3, col4 = st.columns(4)
    
    with col2:
        if st.button(":point_left: A is better", use_container_width=True):
            st.session_state.selection = 1
    
    with col3:
        if st.button(":point_right: B is better", use_container_width=True):
            st.session_state.selection = 0
    
    _, col, _ = st.columns([1,1,1])
    with col:
        if st.button("Next question →", use_container_width=True):
            if st.session_state.selection is not None:
                elapsed_time = int(time.perf_counter() - st.session_state.start_time)
                st.session_state.last_response_id += 1
                new_row = [datetime.now(), st.session_state.last_response_id, st.session_state.eval_id, base_claim_id, left_narrative_id, right_narrative_id, kpi_id, st.session_state.selection, elapsed_time]
                current_data = pd.DataFrame(st.session_state.eval_connection.read(worksheet="evaluations", ttl=1))
                current_data.loc[st.session_state.last_response_id] = new_row
                st.session_state.eval_connection.update(worksheet="evaluations", data=current_data)
                st.session_state.start_time = None
                st.session_state.selection = None
                st.rerun()
            else:
                st.warning("Please select an option.")

if __name__ == "__main__":
    if 'eval_id' not in st.session_state:
        login()
    else:
        main()