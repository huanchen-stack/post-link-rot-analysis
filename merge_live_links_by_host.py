import os
import json
from urllib.parse import urlparse


DIRS = [f"edit_history/edit_history_{i}" for i in range(1, 5)]
O_DIR = "probe/probe_live/"
YEAR = "2019"
print(DIRS)

os.makedirs(O_DIR, exist_ok=True)

MERGED = {}

def process_files(folder_path):
    global MERGED

    for filename in os.listdir(folder_path):
        if filename.endswith(f"-{YEAR}-external-links.json"):
            article_name = filename.replace(f"-{YEAR}-external-links.json", "")
            ext_file_path = os.path.join(folder_path, filename)
            
            with open(ext_file_path, "r") as f:
                ext_allinks = json.load(f)
            
            for link in ext_allinks["live_links"]:
                hostname = urlparse(link).hostname
                if hostname not in MERGED:
                    MERGED[hostname] = {
                        "total_links": 0,
                        "live_links": []
                    }
                
                MERGED[hostname]["total_links"] += 1
                MERGED[hostname]["live_links"].append({
                    "url": link,
                    "folder_path": folder_path,
                    "article_name": article_name
                })

if __name__ == "__main__":
    for dir_ in DIRS:
        process_files(dir_)

    with open(f"{O_DIR}merged_live_links_by_host.json", "w") as f:
        json.dump(MERGED, f, indent=4)
    
    merged_meta = [(k, v["total_links"]) for k, v in MERGED.items()]
    merged_meta = sorted(merged_meta, key=lambda x: x[1], reverse=True)
    merged_meta = {e[0]: e[1] for e in merged_meta}
    with open(f"{O_DIR}merged_live_links_by_host_meta.json", "w") as f:
        json.dump(merged_meta, f, indent=4)