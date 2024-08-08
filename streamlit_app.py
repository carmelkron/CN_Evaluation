import streamlit as st
import pandas as pd

st.title("Counter-Narrative Evaluation")
st.write(
    "Let's start building! For help and inspiration, head over to [docs.streamlit.io](https://docs.streamlit.io/)."
)

st.write("I'm Carmel and i changed this file. Can you see it?")

st.write(pd.read_csv('cn_dataset_LLAMA.csv'))
