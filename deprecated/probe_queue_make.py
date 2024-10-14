import json
import random

def schedule_links(metadata_file, merged_file, output_file):
    """Schedules no more than 50 links per hostname and spreads them evenly into a final list."""
    
    # Load the metadata and merged by hostname data
    with open(metadata_file, "r", encoding="utf-8") as meta_file:
        metadata = json.load(meta_file)
    
    with open(merged_file, "r", encoding="utf-8") as merged_file_data:
        merged_data = json.load(merged_file_data)
    
    # Final list to hold the scheduled links
    final_scheduled_links = []
    
    # Iterate through the metadata
    for host_meta in metadata:
        host = host_meta['host']
        # Get the links for the hostname
        links = merged_data.get(host, [])
        
        # Limit to 50 links or fewer if less than 50 exist
        selected_links = random.sample(links, min(len(links), 50))
        
        # Append selected links to the final list
        final_scheduled_links.extend(selected_links)
    
    # Shuffle the final list to ensure even distribution across hostnames
    random.shuffle(final_scheduled_links)


    #####################################################
    final_scheduled_links = final_scheduled_links[:1000]
    #####################################################


    # Save the final scheduled links to the output file
    with open(output_file, "w", encoding="utf-8") as outfile:
        json.dump(final_scheduled_links, outfile, indent=4)

    print(f"Scheduled links saved to {output_file}")

# Example usage
metadata_file = "merged_by_hostname_metadata_2014.json"  # Replace with your metadata file
merged_file = "merged_by_hostname_2014.json"   # Replace with your merged file by hostname
output_file = "probe_queue_2014.json"      # Output file for the scheduled links

# Schedule the links and save to the output file
schedule_links(metadata_file, merged_file, output_file)
