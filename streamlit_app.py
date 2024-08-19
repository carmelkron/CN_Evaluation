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
st.session_state.df = pd.DataFrame(data)

# Function to get a random base claim and its counter-narratives from two different propagnda techniques
def get_random_claim_and_responses():
    random_base_claim = np.random.choice(st.session_state.df['base_claim'].unique())
    relevant_counter_narratives = st.session_state.df[st.session_state.df['base_claim'] == random_base_claim].reset_index(drop=True)
    two_random_techniques = np.random.choice(relevant_counter_narratives['propaganda_technique_name'].unique(), size=2, replace=False)
    first_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[0]].sample(n=1).reset_index(drop=True)
    second_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[1]].sample(n=1).reset_index(drop=True)
    cn_pair = pd.concat([first_cn, second_cn], ignore_index=True)
    return random_base_claim, relevant_counter_narratives, cn_pair

# Function to update counter
def update_counter(question_number, response_id):
    col_name = f'q{question_number}_counter'
    st.session_state.df[col_name] = pd.to_numeric(st.session_state.df[col_name], errors='coerce')
    val = st.session_state.df[st.session_state.df['response_id'] == response_id][col_name].iloc[0]
    st.session_state.df.loc[st.session_state.df['response_id'] == response_id, col_name] = val + 1
    conn.update(worksheet="cn_dataset_LLAMA", data=st.session_state.df)

# Main app
def main():
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    if st.session_state.random_base_claim is None or (st.session_state.current_question > 3):
        st.session_state.random_base_claim, st.session_state.relevant_counter_narratives, st.session_state.cn_pair = get_random_claim_and_responses()
        st.session_state.selections = {}
        st.session_state.current_question = 1
        st.session_state.pending_updates = []
    
    st.markdown(f"<h5 style='text-align:center;'>Number of evaluations so far: {st.session_state.counter}</h5>", unsafe_allow_html=True)
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
        
        # Get the length of both button texts, ensuring they are strings
        text_a = str(st.session_state.cn_pair.loc[0, 'response_text'])
        text_b = str(st.session_state.cn_pair.loc[1, 'response_text'])
        max_length = max(len(text_a), len(text_b))
        
        # CSS to make buttons the same size
        button_style = f"""
        <style>
        .stButton > button {{
            width: 100%;
            height: {max_length // 30}em;  # Adjust this calculation as needed
            white-space: normal;
            word-wrap: break-word;
        }}
        </style>
        """
        st.markdown(button_style, unsafe_allow_html=True)
        
        with col1:
            st.markdown(f"<h5 style='text-align:center;'>A</h5>", unsafe_allow_html=True)
            if st.button(text_a, key=f"q{q_num}_a"):
                st.session_state.selections[q_num] = 'A'
        
        with col2:
            st.markdown(f"<h5 style='text-align:center;'>B</h5>", unsafe_allow_html=True)
            if st.button(text_b, key=f"q{q_num}_b"):
                st.session_state.selections[q_num] = 'B'
        
        # Continue button below the two columns
        _, col2, _ = st.columns([1,1,1])
        with col2:
            if st.button("Continue", key=f"continue_{q_num}"):
                if q_num in st.session_state.selections:
                    st.session_state.counter += 1
                    selected_option = st.session_state.selections[q_num]
                    response_id = st.session_state.cn_pair.loc[0 if selected_option == 'A' else 1, 'response_id']
                    st.session_state.pending_updates.append((q_num, response_id))
                    if q_num < 3:
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        for question, response_id in st.session_state.pending_updates:
                            update_counter(question, response_id)
                            data = conn.read(worksheet="cn_dataset_LLAMA")
                            st.session_state.df = pd.DataFrame(data)
                        st.session_state.current_question = 4  # This will trigger a new claim on the next run
                        st.rerun()
                else:
                    st.warning("Please select an option before continuing.")
    else:
        st.success("You've completed all questions for this claim. A new claim will be presented.")
        st.session_state.random_base_claim = None  # Reset to trigger new claim generation
        st.rerun()

if __name__ == "__main__":
    main()