from langchain_openai import ChatOpenAI
from my_translator import settings
import concurrent.futures
from os import walk

llm = ChatOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    model="gemini-2.5-flash-preview-05-20",
    api_key=settings.API_KEY,
)


def checker(text, llm):
    request = "do you think is this .srt file ok and normal? just answer yes/no:\n" + text
    response = llm.invoke(request).content
    if "no" in response.lower():
        return False
    return True


def read(path):
    text = ""
    with open(path, 'r') as reader:
        return reader.read()


def write(path, text):
    with open(path, 'w') as writer:
        writer.write(text)


def translate(import_path, export_path, lang, conversational, filename, llm, index):
    error = {}
    try:
        text = read(f'{import_path}/{filename}')

        if conversational:
            conversational = "conversational"
        else:
            conversational = ""

        request = (f"translate this .srt file to {conversational} {lang} Conceptual and accurate And revise the sentence structures to make them clear, just give the result:\n") + text

        response = llm.invoke(request).content
        write(f'{export_path}/{filename}', response)
        error['state'] = True
        error["message"] = f'file {index+1}: {filename} completed'

    except Exception as e:
        error['state'] = False
        if "403" in str(e):
            error["message"] = "please try with a VPN."
        else:
            error["message"] = e

    return error


def gemini_translate(import_path, export_path):
    files = []
    for _, _, filenames in walk(import_path):
        files = filenames
        break

    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for index, filename in enumerate(files):
            futures.append(executor.submit(translate, import_path, export_path, filename, llm, index))

        for index, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            print(result["message"])
