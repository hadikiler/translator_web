from langchain_openai import ChatOpenAI
from os import walk
from pathlib import Path
from google import genai

# MODEL = "gemini-2.5-pro"  # Input token 1,000,000, Output token limit 65,536
MODEL = "gemini-2.5-flash"  # Input token 1,000,000, Output token limit 65,536
# MODEL = "gemini-2.0-flash"  # Output token limit 8,192


API_KEY = "AIzaSyDR49YtJPhn0QJB8Jh6FZM4gSliW9W47xg"


def read(path):
    with open(path, 'r') as reader:
        return reader.read()


def write(path, text):
    with open(path, 'w') as writer:
        writer.write(text)


def send_request(request, api_key):
    if api_key == "" or len(api_key) < 8:
        api_key = API_KEY
    client = genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=MODEL, contents=request
    )
    return response.text


def translate(text, api_key, lang, conversational):
    if conversational:
        conversational = "conversational"
    else:
        conversational = ""

    request = f"""Please translate this .srt file into {conversational} {lang} with accurate and meaningful interpretation.
     Also, revise the sentence structures to make them clearer and easier to read, just give the result:\n\n""" + text
    return send_request(request, api_key)
