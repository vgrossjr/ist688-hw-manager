import streamlit as st
from openai import OpenAI
import pymupdf

st.title("HW1")
st.write("Upload a .txt or .pdf file and OpenAI will summarize it.")

# Sidebar: choose the type of summary
summary_type = st.sidebar.selectbox(
    "Type of summary",
    [
        "Summarize the document in 100 words",
        "Summarize the document in 2 connecting paragraphs",
        "Summarize the document in 5 bullet points",
    ],
)

# Sidebar section: choose which OpenAI model to use
st.sidebar.subheader("Model")
model_choice = st.sidebar.radio(
    "Choose a model",
    ["GPT-6 Luna", "GPT-6.1 Terra", "GPT-6.1 Sol"],
)
if model_choice == "GPT-6 Luna":
    model = "gpt-6-luna"
elif model_choice == "GPT-6.1 Terra":
    model = "gpt-6.1-terra"
else:
    model = "gpt-6.1-sol"
st.sidebar.caption(f"Using: {model}")

# 1. Get the OpenAI API key from Streamlit secrets.
#    Locally it comes from .streamlit/secrets.toml (which Git ignores).
#    On Streamlit Community Cloud it comes from the app's Secrets settings.
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except Exception:
    st.error("No OpenAI API key found. Add OPENAI_API_KEY to your Streamlit secrets.")
    st.stop()

# 2. Turn the summary type into instructions for the LLM
if summary_type == "Summarize the document in 100 words":
    instructions = "Summarize the document in about 100 words."
elif summary_type == "Summarize the document in 2 connecting paragraphs":
    instructions = (
        "Summarize the document in exactly 2 paragraphs. "
        "The second paragraph should follow on naturally from the first."
    )
else:
    instructions = "Summarize the document in exactly 5 bullet points."

instructions = instructions + " Use only the information in the document."


# Read all the text out of a PDF file, one page at a time, using PyMuPDF
def read_pdf(file):
    pdf = pymupdf.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in pdf:
        text = text + page.get_text() + "\n"
    pdf.close()
    return text


# 3. Let the user upload a document. Only .txt and .pdf files are allowed.
uploaded_file = st.file_uploader("Upload a document (.txt or .pdf)", type=["txt", "pdf"])

# 4. As soon as a document is uploaded, read it and show the summary.
#    The document is only kept in a normal variable while the page runs.
#    It is not saved to st.session_state or a cache, so when the user removes
#    the file from the uploader, uploaded_file becomes None and the app no
#    longer has access to the file's data.
if uploaded_file is not None:
    file_extension = uploaded_file.name.split(".")[-1].lower()
    document = None

    if file_extension == "txt":
        document = uploaded_file.read().decode("utf-8", errors="replace")
    elif file_extension == "pdf":
        document = read_pdf(uploaded_file)
    else:
        st.error("Unsupported file type.")

    if document is not None and document.strip() == "":
        st.error("No text could be read from this file.")
    elif document is not None:
        try:
            client = OpenAI(api_key=api_key)
            with st.spinner("Summarizing..."):
                response = client.responses.create(
                    model=model,
                    instructions=instructions,
                    input=f"Here is the document:\n\n{document}",
                )

            # 5. Show the summary
            st.subheader("Summary")
            st.write(response.output_text)
        except Exception as error:
            st.error(f"Something went wrong: {error}")
