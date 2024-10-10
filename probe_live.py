import json
import broken
import os

def process_queue(input_file, output_file, start_index=0):
    # Load the probe queue data
    with open(input_file, "r", encoding="utf-8") as infile:
        probe_queue = json.load(infile)
    # probe_queue = probe_queue[:5]

    # Process each element starting from the specified index
    for index in range(start_index, len(probe_queue)):
        entry = probe_queue[index]
        url = entry["url"]
        
        # Check if the URL is broken
        is_broken, reason = broken.broken(url)
        
        # Add the results to the entry
        entry["is_broken"] = is_broken
        entry["reason"] = reason
        
        # Write the processed entry to the output file
        with open(output_file, "a", encoding="utf-8") as outfile:
            json.dump(entry, outfile)
            outfile.write("\n")  # Ensure each entry is on a new line
        
        # Print the progress
        print(f"Processed {index + 1}/{len(probe_queue)}: {url}", flush=True)
        
        # Save the progress in case of interruption
        last_processed_index = index + 1

    print("Processing completed.")

# Example usage
input_file = "probe_queue_2014.json"
output_file = "probe_results_2014.json"
start_index = 0  # Adjust this if you need to resume from a specific index

process_queue(input_file, output_file, start_index)
