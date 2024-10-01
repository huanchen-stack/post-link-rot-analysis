import mwparserfromhell
import os
import json

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
        if filename.endswith("-2019.txt"):
            article_name = filename.replace("-2019.txt", "")
            txt_file_path = os.path.join(folder_path, filename)
            json_file_path = os.path.join(folder_path, f"{article_name}-2019-external-links.json")
            
            # Read the .txt file
            with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                article_text = txt_file.read()
            
            # Extract external links
            external_links = extract_external_links(article_text)
            
            # Save external links to JSON file
            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump({"external_links": external_links}, json_file, indent=4)
            
            print(f"Extracted and saved external links for {article_name}.")

# Set the folder path where your files are stored
folder_path = "edit_history_2"

# Process the files
process_files(folder_path)