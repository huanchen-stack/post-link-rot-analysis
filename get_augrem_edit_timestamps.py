import json
from concurrent.futures import ThreadPoolExecutor

with open("edit_history/iter/iter_edit_history_results.json", "r") as f:
    data = f.readlines()
    data = [json.loads(line.strip()) for line in data]


critical_data = {}

def get_augrem_edit_timestamps(d):
    critical_timestamps = []
    if "augmentation" in d and "edit_meta" in d["augmentation"] and d["augmentation"]["edit_meta"]:
        critical_timestamps.append({
            "type": "augmentation",
            "timestamp": d["augmentation"]["edit_meta"]["timestamp"]
        })
    if "remove-purposely" in d and len(d["remove-purposely"]) > 0:
        last_removal = d["remove-purposely"][-1]
        if "edit_meta_from" in last_removal and not "edit_meta_to" in last_removal:
            critical_timestamps.append({
                "type": "removal",
                "timestamp": last_removal["edit_meta_from"]["timestamp"]
            })
    return d["folder_path"], d["article_name"], d["url"], critical_timestamps

with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(get_augrem_edit_timestamps, d) for d in data]
    for future in futures:
        folder_path, article_name, url, critical_timestamps = future.result()
        if folder_path not in critical_data:
            critical_data[folder_path] = {}
        if article_name not in critical_data[folder_path]:
            critical_data[folder_path][article_name] = {}
        critical_data[folder_path][article_name][url] = critical_timestamps

with open("edit_history/iter/iter_augrem_edit_timestamps.json", "w") as f:
    json.dump(critical_data, f)

