import streamlit as st
import pandas as pd
import numpy as np
import random
from streamlit_gsheets import GSheetsConnection

# Set up the page
st.set_page_config(layout="wide")

# Initialize session state
if 'random_base_claim' not in st.session_state:
    st.session_state.random_base_claim = None
    st.session_state.relevant_counter_narratives = None
    st.session_state.cn_pair = None
    st.session_state.selections = {}

# Load the data
conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(worksheet="cn_dataset_LLAMA")
df = pd.DataFrame(data)

# Function to get a random base claim and its counter-narratives from two different propagnda techniques
def get_random_claim_and_responses():
    random_base_claim = np.random.choice(df['base_claim'].unique())
    relevant_counter_narratives = df[df['base_claim'] == random_base_claim].reset_index(drop=True)
    two_random_techniques = np.random.choice(relevant_counter_narratives['propaganda_technique_name'].unique(), size=2, replace=False)
    first_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[0]].sample(n=1).reset_index(drop=True)
    second_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[1]].sample(n=1).reset_index(drop=True)
    cn_pair = pd.concat([first_cn, second_cn], ignore_index=True)
    return random_base_claim, relevant_counter_narratives, cn_pair

# Function to update counter
def update_counter(question_number, response_id):
    col_name = f'q{question_number}_counter'
    val = df[df['response_id'] == response_id][col_name]
    df.loc[df['response_id'] == response_id, col_name] = val + 1
    conn.update(worksheet="dataset_evaluation", data=df)

# Main app
def main():
    if st.session_state.random_base_claim is None or (st.session_state.current_question > 3):
        st.session_state.random_base_claim, st.session_state.relevant_counter_narratives, st.session_state.cn_pair = get_random_claim_and_responses()
        st.session_state.selections = {}
        st.session_state.current_question = 1
        st.session_state.pending_updates = []
    
    st.markdown(f"<h2 style='text-align:center;'>Here is a claim that is often claimed by {st.session_state.relevant_counter_narratives.loc[0, 'claimed_by']}:</h2>", unsafe_allow_html=True)
    st.markdown(f'### <p style="color:red; font-size:28px;">"{st.session_state.random_base_claim}"</p>', unsafe_allow_html=True)
    
    # Define the three questions
    questions = [
        "Which do you find more convincing as a rebuttal to the opinion displayed above, A or B?",
        "Which evokes stronger emotions, A or B?",
        "Which do you think the average social media user is more likely to find interesting to share (repost/retweet), A or B?"
    ]
    
    # Display current question
    q_num = st.session_state.current_question
    if q_num <= 3:
        st.markdown(f'### <p style="font-size:24px; text-align:center; font-weight:bold;"> {questions[q_num-1]} </p>', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"<h5 style='text-align:center;'>A</h5>", unsafe_allow_html=True)
            if st.button(f"{st.session_state.cn_pair.loc[0, 'response_text']}", key=f"q{q_num}_a", disabled=q_num in st.session_state.selections):
                st.session_state.selections[q_num] = 'A'
                st.session_state.pending_updates.append((q_num, st.session_state.cn_pair.index[0]))
                st.success("Response recorded!")
        
        with col2:
            st.markdown(f"<h5 style='text-align:center;'>B</h5>", unsafe_allow_html=True)
            if st.button(f"{st.session_state.cn_pair.loc[1, 'response_text']}", key=f"q{q_num}_b", disabled=q_num in st.session_state.selections):
                st.session_state.selections[q_num] = 'B'
                st.session_state.pending_updates.append((q_num, st.session_state.cn_pair.loc[1, 'response_id']))
                st.success("Response recorded!")
        
        if q_num in st.session_state.selections:
            if q_num < 3:
                if st.button("Continue"):
                    st.session_state.current_question += 1
                    st.rerun()
            else:  # For the third question
                if st.button("Continue to Next Claim"):
                    for question, response_id in st.session_state.pending_updates:
                        update_counter(question, response_id)
                    st.session_state.current_question = 4  # This will trigger a new claim on the next run
                    st.rerun()
    else:
        st.success("You've completed all questions for this claim. Click 'Continue to Next Claim' to proceed.")
        if st.button('Continue to Next Claim'):
            st.session_state.current_question = 4  # This will trigger a new claim on the next run
            st.rerun()

if __name__ == "__main__":
    main()