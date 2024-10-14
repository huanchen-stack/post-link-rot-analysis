import json
from collections import defaultdict
import os


I_FILE = "probe/probe_live/probe_live_results_broken.json"
O_FILE = "edit_history/iter/probe_live_broken_links.json"

os.makedirs("edit_history/iter/", exist_ok=True)

def group_links_by_article(input_file, output_file):

    grouped_data = defaultdict(lambda: defaultdict(lambda: {"number_of_links": 0, "list_of_links": []}))

    with open(input_file, "r", encoding="utf-8") as infile:
        data = json.load(infile)
    
    for entry in data:
        folder = entry["folder_path"]
        article = entry["article_name"]
        
        grouped_data[folder][article]["number_of_links"] += 1
        grouped_data[folder][article]["list_of_links"].append(entry)
    
    final_output = {folder: dict(articles) for folder, articles in grouped_data.items()}

    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(final_output, outfile, indent=4)
    
    unique_combinations = sum(len(articles) for articles in grouped_data.values())
    print(f"Total number of unique <dir, article> pairs: {unique_combinations}")

# Example usage

if __name__ == "__main__":
    group_links_by_article(I_FILE, O_FILE)
