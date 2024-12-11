import polib
import deepl
import openai
from deep_translator import GoogleTranslator, ChatGptTranslator, DeeplTranslator
import getopt
import sys
import re
import time
from concurrent.futures import ThreadPoolExecutor

CHATGPT_API_TOKEN = 'PUT YOUR API HERE'
DEEPL_API_TOKEN = 'PUT YOUR API HERE'

bIsUsingChatGPT = False
bIsUsingDeepL = True
bIsUsingFreeDeepL = True

batch_size = 3
api_delay = 0.2

# Global variables
argv = sys.argv[1:]
opts, args = getopt.getopt(argv, "f:l:")

def translate(texts, lang):
    # Define a dictionary to hold the mappings of tokens to placeholders
    placeholders = {}
    
    # print(f"Translating: {texts}")
    try:

        if bIsUsingChatGPT:
            translated_texts = ChatGptTranslator(api_key=CHATGPT_API_TOKEN, target=lang).translate_batch(texts)
        elif bIsUsingDeepL:
            translated_texts = DeeplTranslator(api_key=DEEPL_API_TOKEN, target=lang, use_free_api=bIsUsingFreeDeepL).translate_batch(texts)
        else:
            # Default Using Google
            translated_texts = GoogleTranslator(source='auto', target=lang).translate_batch(texts)
        
        # Check if the translation was successful
        if len(translated_texts) > 0:  # Ensure there are translated texts
            print(f"Translated: {texts} -> {translated_texts}\n")
        else:
            print(f"No translation received for: {texts}")
            translated_texts = ["TRANSLATION_ERROR"]

    except Exception as e:
        print(f"Error translating text: {e}")
        # If translation fails, return the original text or an error message
        translated_texts = ["TRANSLATION_ERROR"]

    return translated_texts

def get_filename():
    filename = None  # Initialize the variable to avoid UnboundLocalError
    # read arguments from command line
    for opt, arg in opts:
        if opt in ['-f']:
            filename = arg
            break  # Exit loop once the filename is found

    if not filename:
        print('Please enter the filename of the PO file e.g. /Unlocalized.po:')
        filename = input()
    return filename

def get_target_language():
    lang = None
    # read arguments from command line
    for opt, arg in opts:
        if opt in ['-l']:
            lang = arg
    if not lang:
        print('Please enter two letter ISO language code e.g. ZH:')
        lang = input()
    return lang

def translate_entry(entries, lang, filename):
     # Collect all msgid values from the array of entries
    msgids = [entry.msgid for entry in entries if not entry.msgstr]
    
    if msgids:
        # Pass the array of msgid values to the translate function
        translations = translate(msgids, lang)
        po = polib.pofile(filename)
        po.save(filename)
        
def batchify(entries):
    #Splits the list of entries into batches of a given size.
    for i in range(0, len(entries), batch_size):
        yield entries[i:i + batch_size]

def process_file(filename, lang):
    po = polib.pofile(filename)
    untranslated_entries = po.untranslated_entries()
    
    # Split the untranslated entries into batches
    batches = list(batchify(untranslated_entries))

    # Use a ThreadPoolExecutor to process translations concurrently
    with ThreadPoolExecutor() as executor:
        futures = []
        for batch in batches:
            futures.append(executor.submit(translate_entry, batch, lang, filename))
            # Add delay between batches
            time.sleep(api_delay)

        # Wait for all threads to complete
        for future in futures:
            future.result()

    # Save the updated PO file
    po.save(filename)

if __name__ == '__main__':
    process_file(get_filename(), get_target_language())
