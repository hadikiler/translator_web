from langchain_openai import *
from dotenv import load_dotenv
from pathlib import Path
from os import walk
import time
import os
import re

load_dotenv()


def parse_srt(content):
    """
    Parse the content of an SRT file into a dictionary
    """
    sections = {}
    parts = re.split(r'\n{2,}', content.strip())
    for part in parts:
        lines = part.splitlines()
        if len(lines) >= 3:
            index = int(lines[0])
            sections[index] = {
                "time": lines[1],
                "text": " ".join(lines[2:]).strip()
            }
    return sections


def check_translate(original, translated):
    """
    Check if the translation contains all sections of the original
    """
    original_sections = parse_srt(original)
    org_length = len(original_sections)
    translated_sections = parse_srt(translated)
    tr_length = len(translated_sections)

    # check for extra part in translation
    if org_length != tr_length:
        return False
    # Check if all keys in the original are present in the translation
    for key in original_sections:
        if key not in translated_sections:
            return False
    return True


def split_srt_string(srt_string, max_length=4096):
    """
    Splits an SRT string into chunks, ensuring full subtitle blocks are preserved.

    Args:
        srt_string (str): The input SRT string.
        max_length (int): The maximum length of each chunk.

    Returns:
        list: A list of SRT chunks, each not exceeding max_length.
    """
    chunks = []
    current_chunk = ""
    current_length = 0

    # Split the SRT string into blocks (split by double newlines)
    blocks = srt_string.strip().split('\n\n')

    for block in blocks:
        block += '\n\n'  # Add back the double newline to preserve format
        block_length = len(block)

        # Check if adding this block exceeds the max_length
        if current_length + block_length > max_length:
            # Save the current chunk and start a new one
            chunks.append(current_chunk.strip())
            current_chunk = block
            current_length = block_length
        else:
            # Add the block to the current chunk
            current_chunk += block
            current_length += block_length

    # Add the last chunk if it has content
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def send_request(llm, request, content, log=False):
    parts = split_srt_string(content, 4096 - len(request))  # split file, max_length is 4096 per request
    full_res = ''
    counter = 0
    for part in parts:
        counter += 1
        if log:
            print('=========================================')
            print(part[:100])
            print('------------------------------')
            print(part[-100:])
            print('=========================================')

        while True:
            # send request, put main content in ``, remove useless symbol
            try:
                response = llm.invoke(request + f"`\n{part}\n`")
            except Exception as e:
                return False

            half_res = response.content.replace('`', '').replace('srt', '', 1)  # delete description and symbols
            if check_translate(part, half_res):
                full_res += ('\n\n' + half_res)  # save them in main text
                break
            print('Some data lost, try again...')
        if not log:
            print(f"translation part{counter} Completed...")
    return full_res


def reader(en_path):
    with open(en_path, 'r') as f:  # Read english file
        return ''.join(f.readlines())


def writer(content, export_path):
    with open(export_path, 'w') as f:
        f.write(content)


def translator(file_path, export_path, api_key, lang='persian', conversational=False):
    result = {}

    llm = ChatOpenAI(
        base_url="https://api.chatanywhere.org",
        model="gpt-4o-mini",
        api_key=api_key,
    )

    if conversational:
        conversational = '`conversational`'
    else:
        conversational = ''

    old_request = f"""
    help me to translate some .srt text to {conversational} {lang},
    as response only write the result (without any symbol),
    remember we need number and times in text to make .srt file,
    don't combine to parts or take care of others time,
    make sure to not lose any translation,
    also don't add or remove anything from text,
    I put the text in `` and the text:\n
    """

    request = f"""
    convert these subtitles in {conversational} {lang} but , i don't mean just translation ,
    you should understand consept of text and rewrite it by yourself. 
    focus on the concepts and making the translation natural , meaningful and fluent.
    I put the text in `` , just give the result and Don't add a part to the translation , their format is .srt:
    """

    content = reader(en_path=file_path)
    full_res = send_request(llm=llm, request=request, content=content)  # translation
    if not full_res:  # if limited
        print('limited...')
        return None

    translated_path = export_path + '/' + f"translated_{os.path.basename(file_path)}"
    writer(content=full_res, export_path=translated_path)
    Path.unlink(Path(file_path))  # delete old
    return translated_path
