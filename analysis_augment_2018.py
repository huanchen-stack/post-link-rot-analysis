import os
import json
from urllib.parse import urlparse

def categorize_links(external_links):
    """Categorizes external links into live and archived."""
    live_links = []
    archived_links = []

    for link in external_links:
        if link.startswith("https://web.archive.org") or link.startswith("http://web.archive.org") or link.startswith("https://archive.org") or link.startswith("http://archive.org"):
            # Check if the archive link contains a timestamp from 2018 or 2019
            parts = link.split('/')
            if len(parts) > 4 and (parts[4].startswith("2018") or parts[4].startswith("2019")):
                pass
            archived_links.append(link)
        else:
            live_links.append(link)
    
    return live_links, archived_links

def extract_article_name(filename):
    """Extracts the article name from the filename (before the year and extension)."""
    return filename.rsplit("-", 1)[0]

def pair_live_and_archived(live_links, archived_links):
    """Pairs live links with their corresponding archived versions and captures non-augmented links."""
    live_to_archive_map = {}
    augmented_count = 0
    not_augmented_count = 0
    non_augmented_links = []  # List to store non-augmented (no paired archive) live links
    
    # Create a mapping between live links and their archived versions
    for live_link in live_links:
        live_url = urlparse(live_link).geturl()
        has_archive = False
        for archive_link in archived_links:
            if live_url in archive_link:
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
    """Appends non-augmented live links to a JSON file with folder path and article name."""
    entries = []
    for link in non_augmented_links:
        entry = {
            "url": link,
            "folder_path": folder_path,
            "article_name": article_name.rstrip("-2019-external")
        }
        entries.append(entry)

    # Check if the file already exists
    if os.path.exists(non_augmented_file):
        # Load the existing content and append the new entries
        with open(non_augmented_file, "r", encoding="utf-8") as file:
            data = json.load(file)
        data.extend(entries)
    else:
        # If the file does not exist, initialize with new entries
        data = entries
    
    # Save the updated content back to the file
    with open(non_augmented_file, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

def process_files(folder_path, non_augmented_file):
    """Processes all external-link files and saves non-augmented live links."""
    total_augmented_count = 0
    total_not_augmented_count = 0
    
    for filename in os.listdir(folder_path):
        if filename.endswith("-external-links.json"):
            json_file_path = os.path.join(folder_path, filename)
            
            # Extract article name from the filename
            article_name = extract_article_name(filename)
            
            # Read the external links from the JSON file
            with open(json_file_path, "r", encoding="utf-8") as json_file:
                data = json.load(json_file)
                external_links = data.get("external_links", [])
            
            # Categorize the links
            live_links, archived_links = categorize_links(external_links)
            
            # Pair live links with archived links and get non-augmented links
            live_to_archive_map, augmented_count, not_augmented_count, non_augmented_links = pair_live_and_archived(live_links, archived_links)
            
            # Save the non-augmented live links to the JSON file
            save_non_augmented_links_to_json(non_augmented_links, folder_path, article_name, non_augmented_file)
            
            # Print stats for this file
            print(f"{filename}: Augmented: {augmented_count}, Not Augmented: {not_augmented_count}")
            
            # Accumulate stats
            total_augmented_count += augmented_count
            total_not_augmented_count += not_augmented_count
    
    # Print final accumulated stats for the folder
    print("\nFinal Stats for the Directory:")
    print(f"Total Augmented Links: {total_augmented_count}")
    print(f"Total Not Augmented Links: {total_not_augmented_count}")


# Set the folder path where your files are stored and the file to save non-augmented links
folder_path = f"edit_history_4"
non_augmented_file = f"non_augmented_links_4_2014.json"

# Process the files and append non-augmented links to the specified JSON file
process_files(folder_path, non_augmented_file)
