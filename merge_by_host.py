import os
import json
from urllib.parse import urlparse

def extract_hostname(url):
    """Extracts the hostname from a URL."""
    parsed_url = urlparse(url)
    return parsed_url.hostname

def merge_files_by_hostname(json_files, output_file, metadata_file):
    """Merges multiple JSON files by hostnames and saves the result and metadata."""
    merged_data = {}
    host_url_count = {}

    # Iterate through each JSON file
    for json_file in json_files:
        with open(json_file, "r", encoding="utf-8") as file:
            data = json.load(file)

            # Iterate through each entry in the current JSON file
            for entry in data:
                url = entry.get("url")
                folder_path = entry.get("folder_path")
                article_name = entry.get("article_name")

                # Extract hostname
                hostname = extract_hostname(url)

                # If the hostname doesn't exist in the merged_data dictionary, initialize it
                if hostname not in merged_data:
                    merged_data[hostname] = []

                # Append the entry to the list associated with the hostname
                merged_data[hostname].append({
                    "url": url,
                    "folder_path": folder_path,
                    "article_name": article_name
                })

                # Count the number of URLs per host
                if hostname not in host_url_count:
                    host_url_count[hostname] = 0
                host_url_count[hostname] += 1

    # Save the merged data to the output JSON file
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(merged_data, outfile, indent=4)

    # Create metadata sorted by the number of URLs per host
    sorted_metadata = sorted(
        [{"host": host, "count": count} for host, count in host_url_count.items()],
        key=lambda x: x["count"], 
        reverse=True
    )

    # Save the metadata to the metadata JSON file
    with open(metadata_file, "w", encoding="utf-8") as metafile:
        json.dump(sorted_metadata, metafile, indent=4)

    print(f"Data merged and saved to {output_file}")
    print(f"Metadata saved to {metadata_file}")

# Example usage
json_files = ["non_augmented_links_1.json", "non_augmented_links_2.json", "non_augmented_links_3.json", "non_augmented_links_4.json"]  # Replace with your actual file names
json_files = ["non_augmented_links_4_2014.json"]
output_file = "merged_by_hostname_2014.json"
metadata_file = "merged_by_hostname_metadata_2014.json"

# Merge the files by hostnames and save the result and metadata
merge_files_by_hostname(json_files, output_file, metadata_file)
