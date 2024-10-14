import mwparserfromhell
import os
import json
import re


DIRS = [f"edit_history/edit_history_{i}" for i in range(1, 5)]
YEAR = "2019"
ARCHIVE_PATTERN = re.compile(r'(https?://(web\.)?archive\.org/web/\d+/)')

def extract_external_links(text):
    wikicode = mwparserfromhell.parse(text)
    external_links = {
        "live_links": [],
        "archived_links": []
    }
    for link in wikicode.filter_external_links():
        url = link.url.strip()
        if ARCHIVE_PATTERN.search(url):
            external_links["archived_links"].append(url)
        else:
            external_links["live_links"].append(url)
    return external_links

def process_files(folder_path):
    live_links_count, archived_links_count = 0, 0
    for filename in os.listdir(folder_path):
        if filename.endswith(f"-{YEAR}.txt"):
            article_name = filename.replace(f"-{YEAR}.txt", "")
            txt_file_path = os.path.join(folder_path, filename)
            json_file_path = os.path.join(folder_path, f"{article_name}-{YEAR}-external-links.json")
            
            with open(txt_file_path, "r", encoding="utf-8") as txt_file:
                article_text = txt_file.read()
            
            external_links = extract_external_links(article_text)
            live_links_count += len(external_links["live_links"])
            archived_links_count += len(external_links["archived_links"])

            with open(json_file_path, "w", encoding="utf-8") as json_file:
                json.dump(external_links, json_file, indent=4)
            
            # print(f"Extracted and saved external links for {article_name}.")
    print(f"[{folder_path}] Total live links: {live_links_count}, archived links: {archived_links_count}")

if __name__ == "__main__":
    for dir_ in DIRS:
        process_files(dir_)
