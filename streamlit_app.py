import streamlit as st
import pandas as pd
import numpy as np
import random

# Initialize session state
if 'random_base_claim' not in st.session_state:
    st.session_state.random_base_claim = None
    st.session_state.relevant_counter_narratives = None
    st.session_state.cn_pair = None
    st.session_state.selections = {}

# Load the data
import streamlit as st
from streamlit_gsheets import GSheetsConnection


conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(worksheet="dataset_evaluation")
df = pd.DataFrame(data)

# Initialize counters if they don't exist
for q in range(1, 4):
    col_name = f'q{q}_counter'
    if col_name not in df.columns:
        df[col_name] = 0
    else:
        df[col_name] = df[col_name].astype(int)

# Set up the page
st.set_page_config(layout="wide")

# Function to get a random base claim and its counter-narratives
def get_random_claim_and_counters():
    random_base_claim = np.random.choice(df['base_claim'].unique())
    relevant_counter_narratives = df[df['base_claim'] == random_base_claim].reset_index(drop=True)
    cn_pair = relevant_counter_narratives.sample(2).reset_index(drop=True)
    return random_base_claim, relevant_counter_narratives, cn_pair

# Function to update counter
def update_counter(question_number, cn_index):
    col_name = f'q{question_number}_counter'
    df.at[cn_index, col_name] = df.at[cn_index, col_name] + 1
    df.to_csv('cn_dataset_LLAMA.csv', index=False)

# Main app
def main():
    if st.session_state.random_base_claim is None or st.button('Continue to Next Claim'):
        st.session_state.random_base_claim, st.session_state.relevant_counter_narratives, st.session_state.cn_pair = get_random_claim_and_counters()
        st.session_state.selections = {}
    
    st.markdown(f"<h2 style='text-align:center;'>Here is a claim that is often claimed by {st.session_state.relevant_counter_narratives.loc[0, 'claimed_by']}:</h2>", unsafe_allow_html=True)
    st.markdown(f'### <p style="color:red; font-size:28px;">"{st.session_state.random_base_claim}"</p>', unsafe_allow_html=True)
    
    # Define the three questions
    questions = [
        "Which do you find more convincing as a rebuttal to the opinion displayed above, A or B?",
        "Which evokes stronger emotions, A or B?",
        "Which do you think the average social media user is more likely to find interesting to share (repost/retweet), A or B?"
    ]
    
    # For each question
    for q_num, question in enumerate(questions, 1):
        st.markdown(f'### <p style="font-size:24px; text-align:center; font-weight:bold;"> {question} </p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"<h5 style='text-align:center;'>A</h5>", unsafe_allow_html=True)
            if st.button(f"{st.session_state.cn_pair.loc[0, 'response_text']}", key=f"q{q_num}_a", disabled=q_num in st.session_state.selections):
                st.session_state.selections[q_num] = 'A'
                update_counter(q_num, st.session_state.cn_pair.index[0])
                st.success("Response recorded!")
        
        with col2:
            st.markdown(f"<h5 style='text-align:center;'>B</h5>", unsafe_allow_html=True)
            if st.button(f"{st.session_state.cn_pair.loc[1, 'response_text']}", key=f"q{q_num}_b", disabled=q_num in st.session_state.selections):
                st.session_state.selections[q_num] = 'B'
                update_counter(q_num, st.session_state.cn_pair.index[1])
                st.success("Response recorded!")
        


if __name__ == "__main__":
    main()