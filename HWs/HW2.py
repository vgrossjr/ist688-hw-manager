import anthropic
import requests
import streamlit as st
from bs4 import BeautifulSoup
from google import genai
from openai import OpenAI

st.title("HW2")
st.write("Enter a web page URL and the selected AI model will summarize it.")

# 1. Let the user enter a URL at the top of the page
url = st.text_input("Web page URL", placeholder="https://example.com/article")

# 2. Sidebar: choose the output language and the type of summary
language = st.sidebar.selectbox(
    "Output language",
    ["English", "Spanish", "French", "Korean", "Chinese (Mandarin)", "Indonesian"],
)
summary_type = st.sidebar.selectbox(
    "Type of summary",
    [
        "Summarize the document in 100 words",
        "Summarize the document in 2 connecting paragraphs",
        "Summarize the document in 5 bullet points",
    ],
)

# 3. Sidebar: choose which LLM to use, and whether to use its advanced model
st.sidebar.subheader("LLM")
llm = st.sidebar.selectbox("Choose an LLM", ["OpenAI", "Claude", "Gemini"])
use_advanced = st.sidebar.checkbox("Use advanced model")

# Each LLM has a basic (faster, cheaper) model and an advanced model,
# and each LLM uses its own API key from Streamlit secrets.
if llm == "OpenAI":
    key_name = "OPENAI_API_KEY"
    if use_advanced:
        model = "gpt-5.5"
    else:
        model = "gpt-5.4-mini"
elif llm == "Claude":
    key_name = "ANTHROPIC_API_KEY"
    if use_advanced:
        model = "claude-opus-5-5"
    else:
        model = "claude-haiku-5-5"
else:
    key_name = "GEMINI_API_KEY"
    if use_advanced:
        # gemini-3.6-flash is the most capable stable Gemini model that works
        # on Google's free tier (gemini-4-argon needs billing turned on).
        model = "gemini-3.6-flash"
    else:
        model = "gemini-3.5-flash-lite"

st.sidebar.caption(f"Using: {model}")

# 4. Get the API key for the selected LLM from Streamlit secrets.
#    Locally they come from .streamlit/secrets.toml (which Git ignores).
#    On Streamlit Community Cloud they come from the app's Secrets settings.
try:
    api_key = st.secrets[key_name]
except Exception:
    st.error(f"No API key found for {llm}. Add {key_name} to your Streamlit secrets.")
    st.stop()

# 5. Turn the summary type and language into instructions for the LLM
if summary_type == "Summarize the document in 100 words":
    instructions = "Summarize the document in about 100 words."
elif summary_type == "Summarize the document in 2 connecting paragraphs":
    instructions = (
        "Summarize the document in exactly 2 paragraphs. "
        "The second paragraph should follow on naturally from the first."
    )
else:
    instructions = "Summarize the document in exactly 5 bullet points."

if language == "Chinese (Mandarin)":
    instructions = instructions + " Write the summary in Mandarin Chinese, using Simplified Chinese characters."
else:
    instructions = instructions + f" Write the summary in {language}."

instructions = instructions + " Use only the information in the document."

# Ask every LLM for the summary alone, so the answers look the same no matter
# which LLM made them (some models like to add "Here is your summary:").
instructions = instructions + (
    " Reply with only the summary itself. Do not add an introduction, a title,"
    " a heading, or any closing remarks."
)


# Make the URL complete. People often type "www.example.com" or
# "example.com" without "https://", so add it when it's missing.
def fix_url(url):
    url = url.strip()
    start = url.lower()
    if not start.startswith("http://") and not start.startswith("https://"):
        url = "https://" + url
    return url


# Read a web page and return its text (or None if it can't be read).
# @st.cache_data remembers the result, so switching the language or summary
# type doesn't download the same page again.
@st.cache_data(ttl=3600)
def read_url_content(url):
    # Some websites (like Wikipedia) refuse requests that don't say what
    # browser or app is asking, so send a simple "User-Agent" header.
    headers = {"User-Agent": "Mozilla/5.0 (HW manager Streamlit app)"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()  # Raise an exception for HTTP errors
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.get_text()
    except requests.RequestException as e:
        print(f"Error reading {url}: {e}")
        return None


# One small function per LLM. Each sends the instructions and the page text
# to its own API and returns the summary as plain text.
def summarize_with_openai(api_key, model, instructions, document):
    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=model,
        instructions=instructions,
        input=f"Here is the document:\n\n{document}",
    )
    return response.output_text


def summarize_with_claude(api_key, model, instructions, document):
    client = anthropic.Anthropic(api_key=api_key)
    request = dict(
        model=model,
        max_tokens=16000,
        system=instructions,
        messages=[{"role": "user", "content": f"Here is the document:\n\n{document}"}],
    )
    if model == "claude-opus-5-5":
        # If Opus declines a request for safety reasons, let the API
        # automatically retry it on another model instead of returning nothing.
        response = client.beta.messages.create(
            **request,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        )
    else:
        response = client.messages.create(**request)

    if response.stop_reason == "refusal":
        return "Claude declined to summarize this page."
    return "".join(block.text for block in response.content if block.type == "text")


def summarize_with_gemini(api_key, model, instructions, document):
    # Give up after 60 seconds (60000 milliseconds) instead of waiting forever
    # when a Gemini model is overloaded.
    client = genai.Client(
        api_key=api_key,
        http_options=genai.types.HttpOptions(timeout=60000),
    )
    response = client.models.generate_content(
        model=model,
        contents=f"Here is the document:\n\n{document}",
        config=genai.types.GenerateContentConfig(system_instruction=instructions),
    )
    return response.text


# Pick the right function for the selected LLM.
# @st.cache_data remembers every summary already made, so switching back to a
# language (or LLM) you already used shows that summary again right away.
# The API key starts with "_" so it is NOT used as part of the cache's memory.
@st.cache_data(ttl=3600)
def summarize(llm, model, instructions, document, _api_key):
    if llm == "OpenAI":
        return summarize_with_openai(_api_key, model, instructions, document)
    elif llm == "Claude":
        return summarize_with_claude(_api_key, model, instructions, document)
    else:
        return summarize_with_gemini(_api_key, model, instructions, document)


# 6. As soon as a URL is entered, read the page and show the summary
if url:
    url = fix_url(url)
    with st.spinner("Reading the web page..."):
        document = read_url_content(url)

    if document is None:
        st.error(f"Could not read {url}. Check that the address is correct.")
    elif document.strip() == "":
        st.error("No text was found on that web page.")
    else:
        try:
            with st.spinner(f"Summarizing with {llm} ({model})..."):
                summary = summarize(llm, model, instructions, document, api_key)

            # 7. Show the summary
            st.subheader(f"Summary ({language})")
            st.caption(f"Made by {llm} using {model}")
            st.write(summary)
        except Exception as error:
            st.error(f"Something went wrong with {llm}: {error}")
