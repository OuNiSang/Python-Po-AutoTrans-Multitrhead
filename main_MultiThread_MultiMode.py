import polib
import deepl
import googletrans
import getopt
import sys
import re
from concurrent.futures import ThreadPoolExecutor
import os

DEEPL_API_TOKEN = ''
USE_GOOGLE_TRANSLATE = True

# Global variables
argv = sys.argv[1:]
opts, args = getopt.getopt(argv, "f:l:g:o:")

output_filename = None

for opt, arg in opts:
    if opt in ['-g']:
        USE_GOOGLE_TRANSLATE = arg.lower() == 'true'
    if opt in ['-o']:
        output_filename = arg

def translate(text, lang):
    # Define a dictionary to hold the mappings of tokens to placeholders
    placeholders = {}

    # Use a regular expression to find all the tokens
    tokens = re.findall(r'%\((.*?)\)s', text)

    # Replace each token with a unique placeholder
    for i, token in enumerate(tokens):
        placeholder = f'__PLACEHOLDER_{i}__'
        placeholders[placeholder] = f'%({token})s'
        text = text.replace(f'%({token})s', placeholder)

    # Perform the translation
    if USE_GOOGLE_TRANSLATE:
        translator = googletrans.Translator()
        translated_text = translator.translate(text, dest=lang).text
    else:
        translator = deepl.Translator(DEEPL_API_TOKEN)
        translated_text = str(translator.translate_text(text, target_lang=lang))

    # Replace the placeholders back with the original tokens
    for placeholder, token in placeholders.items():
        translated_text = translated_text.replace(placeholder, token)

    return translated_text

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

def generate_output_filename(input_filename, lang):
    base, ext = os.path.splitext(input_filename)
    # Check if the input file already has a language code
    match = re.match(r'(.*)_([A-Z]{2})$', base)
    if match:
        base = match.group(1)  # Remove existing language code
    return f"{base}_{lang.upper()}{ext}"

def translate_entry(entry, lang):
    if not entry.msgstr:
        print(f"Translating: {entry.msgid}")
        entry.msgstr = translate(entry.msgid, lang)
        print(f"Translated: {entry.msgstr}\n")

def process_file(filename, lang):
    po = polib.pofile(filename)
    untranslated_entries = po.untranslated_entries()

    # Use a ThreadPoolExecutor to process translations concurrently
    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(translate_entry, entry, lang) for entry in untranslated_entries]

        # Wait for all threads to complete
        for future in futures:
            future.result()

    # Determine output file path
    output_path = output_filename if output_filename else generate_output_filename(filename, lang)
    po.save(output_path)
    print(f"Translation saved to: {output_path}")

if __name__ == '__main__':
    process_file(get_filename(), get_target_language())
