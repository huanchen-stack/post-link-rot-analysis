import json
from collections import defaultdict

def group_links_by_article(input_file, output_file):
    # Create a dictionary to hold the grouped data
    grouped_data = defaultdict(lambda: defaultdict(lambda: {"number_of_links": 0, "list_of_links": []}))

    # Load the broken results from the input file
    with open(input_file, "r", encoding="utf-8") as infile:
        data = json.load(infile)
    
    # Group links by folder_path and article_name
    for entry in data:
        folder = entry["folder_path"]
        article = entry["article_name"]
        url = entry["url"]
        
        # Increment the number of links and append the URL to the list
        grouped_data[folder][article]["number_of_links"] += 1
        grouped_data[folder][article]["list_of_links"].append(url)
    
    # Convert defaultdict to regular dict for saving as JSON
    final_output = {folder: dict(articles) for folder, articles in grouped_data.items()}

    # Save the processed data to the output file
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(final_output, outfile, indent=4)
    
    # Print the number of unique <dir, article> pairs
    unique_combinations = sum(len(articles) for articles in grouped_data.values())
    print(f"Total number of unique <dir, article> pairs: {unique_combinations}")

# Example usage
input_file = "probe_results_broken.json"
output_file = "grouped_broken_links.json"

group_links_by_article(input_file, output_file)
