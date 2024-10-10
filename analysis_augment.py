import os
import json
from urllib.parse import urlparse
import re

YEAR = 2014
DIR = "edit_history_4"
O_FILE = "non_augmented_links_4_2014.json"

def categorize_links(external_links):
    live_links = []
    archived_links = []

    archive_pattern = re.compile(r'^https?://(web\.)?archive\.org')
    for link in external_links:
        if archive_pattern.match(link):
            archived_links.append(link)
        else:
            live_links.append(link)
    
    return live_links, archived_links

def extract_article_name(filename):
    return filename.rsplit("-", 1)[0]

def pair_live_and_archived(live_links, archived_links):
    live_to_archive_map = {}
    augmented_count = 0
    not_augmented_count = 0
    non_augmented_links = []

    for live_link in live_links:
        has_archive = False
        for archive_link in archived_links:
            if live_link in archive_link:
                live_to_archive_map[live_link] = archive_link
                augmented_count += 1
                has_archive = True
                break
        
        if not has_archive:
            live_to_archive_map[live_link] = None
            non_augmented_links.append(live_link)
            not_augmented_count += 1
    
    return live_to_archive_map, augmented_count, not_augmented_count, non_augmented_links

def save_non_augmented_links_to_json(non_augmented_links, folder_path, article_name, non_augmented_file):
    entries = []
    for link in non_augmented_links:
        entry = {
            "url": link,
            "folder_path": folder_path,
            "article_name": article_name.rstrip(f"-{YEAR}-external")
        }
        entries.append(entry)
    
    if os.path.exists(non_augmented_file):
        with open(non_augmented_file, 'r') as f:
            data = json.load(f)
        data.extend(entries)
    else:
        data = entries

    with open(non_augmented_file, 'w') as f:
        json.dump(data, f, indent=4)

def process_files(folder_path, non_augmented_file):
    total_augmented_count = 0
    total_not_augmented_count = 0
    
    for filename in os.listdir(folder_path):
        if filename.endswith(f"-{YEAR}-external-links.json"):
            json_file_path = os.path.join(folder_path, filename)
            
            article_name = extract_article_name(filename)
            
            with open(json_file_path, 'r') as f:
                data = json.load(f)
                external_links = data.get('external_links', [])
            
            live_links, archived_links = categorize_links(external_links)
            
            live_to_archive_map, augmented_count, not_augmented_count, non_augmented_links = pair_live_and_archived(live_links, archived_links)
            print(len(non_augmented_links))
            save_non_augmented_links_to_json(non_augmented_links, folder_path, article_name, non_augmented_file)
            
            total_augmented_count += augmented_count
            total_not_augmented_count += not_augmented_count
    
    print(f"Total augmented links: {total_augmented_count}")
    print(f"Total non-augmented links: {total_not_augmented_count}")


if __name__ == "__main__":
    process_files(DIR, O_FILE)