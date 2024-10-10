import mwparserfromhell
import os
import json

YEAR = "2014"

def extract_external_links(text):
    """Extracts external links from wikicode text."""
    wikicode = mwparserfromhell.parse(text)
    external_links = []
    
    # Extract all external links using mwparserfromhell's filter method
    for link in wikicode.filter_external_links():
        external_links.append(str(link))
    
    return external_links

def process_files(folder_path):
    """Processes all .txt files in the folder, extracting external links and saving to JSON."""
    for filename in os.listdir(folder_path):
        if filename.endswith(f"-{YEAR}.txt"):
            article_name = filename.replace(f"-{YEAR}.txt", "")
            txt_file_path = os.path.join(folder_path, filename)
            json_file_path = os.path.join(folder_path, f"{article_name}-{YEAR}-external-links.json")
            
            # Read the .txt file
            with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                article_text = txt_file.read()
            
            # Extract external links
            external_links = extract_external_links(article_text)

            external_links = [l.lstrip('[').rstrip(']').split()[0] for l in external_links]
            
            # Save external links to JSON file
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump({"external_links": external_links}, json_file, indent=4)
            
            print(f"Extracted and saved external links for {article_name}.")

# Set the folder path where your files are stored
folder_path = "edit_history_4"

# Process the files
process_files(folder_path)
