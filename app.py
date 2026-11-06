import streamlit as st

# HW manager: the entry point for all homework pages.
# It lists the pages and runs the one the user picks from the sidebar.
#
# The sidebar shows the pages in the same order as the list below, top to
# bottom. When you add a new homework, add it to the END of the list so it
# appears under the last one.
#
# The homework files live in the "HWs" folder. (Don't name a folder "pages":
# Streamlit treats that name specially and would list its files
# alphabetically instead of in this order.)

st.set_page_config(page_title="HW manager")
st.sidebar.title("HW manager")

hw1 = st.Page("HWs/HW1.py", title="HW1")
hw2 = st.Page("HWs/HW2.py", title="HW2")

page = st.navigation([hw1, hw2])
page.run()
