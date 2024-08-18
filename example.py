import pandas as pd
import streamlit as st
from streamlit_gsheets import GSheetsConnection


conn = st.connection("gsheets", type=GSheetsConnection)

data = conn.read(worksheet="dataset_evaluation")
df = pd.DataFrame(data)

st.write("hello")