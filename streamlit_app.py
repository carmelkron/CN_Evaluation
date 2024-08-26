import streamlit as st
import pandas as pd
import numpy as np
import time
from streamlit_gsheets import GSheetsConnection

# Set up the page
st.set_page_config(layout="wide")
custom_margins = """
<style>
    body {
        overflow-y: scroll;
    }
    .main {
        padding-left: 5%;
        padding-right: 5%;
    }
</style>
"""
st.markdown(custom_margins, unsafe_allow_html=True)
global conn
conn = st.connection("gsheets", type=GSheetsConnection)
# Initialize session state
if 'random_base_claim' not in st.session_state:
    st.session_state.random_base_claim = None
    st.session_state.cn_pair = None
    st.session_state.selections = {}
    st.session_state.question_count = 0
if 'all_updates' not in st.session_state:
    st.session_state.all_updates = []

# Set the number of questions before completion (can be changed as needed)
TOTAL_QUESTIONS = 20

# Load the data
def get_latest_df():
    print("Attempting to read data from Google Sheets...")
    # Force a fresh read by clearing the connection's cache
    if hasattr(conn, '_cached'):
        conn._cached.clear()

    # Add a small delay to ensure the sheet has time to update
    time.sleep(5)
    timestamp = int(time.time())
    # Read the data
    try:
        data = conn.read(worksheet="cn_dataset_LLAMA", ttl=5)
        df = pd.DataFrame(data)
    except Exception as e:
        print(f"Error reading data from Google Sheets: {str(e)}")
        return pd.DataFrame()  # Return an empty DataFrame if read fails

    # Add debugging information
    print(f"Data read from sheet. Shape: {df.shape}")
    print(f"Columns: {df.columns}")

    # Check if 'version' column exists
    if 'version' not in df.columns:
        print("'version' column not found. Adding it with default value 1.")
        df['version'] = 1
    else:
        print("'version' column found. Processing it.")
        df['version'] = pd.to_numeric(df['version'], errors='coerce').fillna(1).astype(int)
        print(f"Version column data: {df['version'].value_counts().sort_index()}")

    print(f"Max version after processing: {df['version'].max()}")

    return df

# Function to get a random base claim and its counter-narratives from two different propaganda techniques
def get_random_claim_and_responses():
    df = get_latest_df()
    random_base_claim = np.random.choice(df['base_claim'].unique())
    relevant_counter_narratives = df[df['base_claim'] == random_base_claim].reset_index(drop=True)
    two_random_techniques = np.random.choice(relevant_counter_narratives['propaganda_technique_name'].unique(), size=2, replace=False)
    first_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[0]].sample(n=1).reset_index(drop=True)
    second_cn = relevant_counter_narratives[relevant_counter_narratives['propaganda_technique_name'] == two_random_techniques[1]].sample(n=1).reset_index(drop=True)
    cn_pair = pd.concat([first_cn, second_cn], ignore_index=True)
    return random_base_claim, cn_pair

def add_update(question_number, response_id):
    st.session_state.all_updates.append((question_number, response_id))

def apply_updates_to_df():
    if st.session_state.all_updates:
        print("Applying updates...")
        df = get_latest_df()
        if df.empty:
            print("Failed to retrieve data. Aborting update.")
            return

        current_version = df['version'].max() if 'version' in df.columns else 0
        print(f"Current max version before updates: {current_version}")

        for question_number, response_id in st.session_state.all_updates:
            col_name = f'q{question_number}_counter'
            if col_name not in df.columns:
                print(f"Adding new column: {col_name}")
                df[col_name] = 0
            
            # Ensure the column is numeric
            df[col_name] = pd.to_numeric(df[col_name], errors='coerce').fillna(0)
            
            matching_rows = df['response_id'] == response_id
            if matching_rows.sum() == 0:
                print(f"Warning: response_id {response_id} not found")
                continue
            
            # Increment the counter
            df.loc[matching_rows, col_name] = pd.Series(df.loc[matching_rows, col_name]).values[0] + 1
            print(f"Incremented {col_name} for response_id {response_id}")

        # Increment version for all rows
        new_version = current_version + 1
        df['version'] = new_version
        
        print(f"New version after updates: {new_version}")
        print(f"Version column data after updates: {df['version'].value_counts().sort_index()}")

        load_df_to_sheets(df)
        st.session_state.all_updates = []  # Clear updates after applying
        print(f"Updates applied and loaded to sheet. New version: {new_version}")
    else:
        print("No updates to apply")

# Function to load df to Google Sheets
def load_df_to_sheets(df):
    print("Saving data to Google Sheets...")
    print(f"Columns being saved: {df.columns}")
    print(f"Shape of data being saved: {df.shape}")
    try:
        conn.update(worksheet="cn_dataset_LLAMA", data=df)
        print("Data successfully saved to Google Sheets")
    except Exception as e:
        print(f"Error saving data to Google Sheets: {str(e)}")

# Main app
def main():
    questions = [
        "Which do you find more convincing as a rebuttal to the opinion displayed above, A or B?",
        "Which evokes stronger emotions, A or B?",
        "Which do you think the average social media user is more likely to find interesting to share (repost/retweet), A or B?"
    ]
    if st.session_state.random_base_claim is None:
        st.session_state.random_base_claim, st.session_state.cn_pair = get_random_claim_and_responses()

    if st.session_state.question_count >= TOTAL_QUESTIONS:
        st.markdown("<h1 style='text-align: center;'>Thank you for your effort!</h1>", unsafe_allow_html=True)
        return

    example_narrative = st.session_state.cn_pair.loc[0]
    pro_what = "pro-Russian" if example_narrative['claimed_by'] == 'Russia' else "pro-Ukrainian"
    
    st.markdown(f"<h4 style='text-align:center;'>Look at this {pro_what} claim</h4>", unsafe_allow_html=True)
    st.markdown(f'<p style="color:red; text-align:center; font-size: 30px;">{st.session_state.random_base_claim}</p>', unsafe_allow_html=True)
    
    q_num = st.session_state.question_count % 3
    st.markdown(f'<h4 style="text-align:center; max-width: 60%; margin: 0 auto;">{questions[q_num]}</h4>', unsafe_allow_html=True)
    
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
        height: 275px;
    }
    """, unsafe_allow_html=True)

    with col1:
        st.markdown("<h2 style='text-align:center;'>A</h2>", unsafe_allow_html=True)
        first_text = st.session_state.cn_pair.loc[0, 'response_text']
        st.markdown(f'<p class="equal-height-paragraph">{first_text}</p>', unsafe_allow_html=True)
        
    with col2:
        st.markdown("<h2 style='text-align:center;'>B</h2>", unsafe_allow_html=True)
        second_text = st.session_state.cn_pair.loc[1, 'response_text']
        st.markdown(f'<p class="equal-height-paragraph">{second_text}</p>', unsafe_allow_html=True)
        
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button(":point_left: A is better", use_container_width=True):
            st.session_state.selections[q_num] = 'A'
    
    with col2:
        if st.button(":point_right: B is better", use_container_width=True):
            st.session_state.selections[q_num] = 'B'
    
    with col3:
        if st.button(":handshake: Tie", use_container_width=True):
            st.session_state.selections[q_num] = 'Tie'
    
    with col4:
        if st.button(":-1: Both are bad", use_container_width=True):
            st.session_state.selections[q_num] = 'Bad'
    
    _, col, _ = st.columns([1,1,1])
    with col:
        if st.button("Next question →", use_container_width=True):
            if st.session_state.selections:
                q_num = st.session_state.question_count % 3 + 1
                if st.session_state.selections[q_num - 1] == 'A':
                    add_update(q_num, str(st.session_state.cn_pair.loc[0, 'response_id']))
                elif st.session_state.selections[q_num - 1] == 'B':
                    add_update(q_num, str(st.session_state.cn_pair.loc[1, 'response_id']))
                elif st.session_state.selections[q_num - 1] == 'Tie':
                    add_update(q_num, str(st.session_state.cn_pair.loc[0, 'response_id']))
                    add_update(q_num, str(st.session_state.cn_pair.loc[1, 'response_id']))
                
                st.session_state.question_count += 1
                
                if st.session_state.question_count % 3 == 0 or st.session_state.question_count >= TOTAL_QUESTIONS:
                    apply_updates_to_df()
                    st.session_state.random_base_claim = None
                
                st.rerun()
            else:
                st.warning("Please select an option.")

if __name__ == "__main__":
    main()