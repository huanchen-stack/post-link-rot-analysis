import json
import os
import re
from removal_reason_filters import FILTERS


I_PATH = "edit_history/iter/results.json"
O_PATH = "probe/probe_archive/probe_archive_scheduled.json"

os.makedirs("probe/probe_archive", exist_ok=True)

with open(I_PATH, 'r') as f:
    results = [json.loads(line) for line in f]

print("All itr results:", len(results))
results = [r for r in results if r["remove-purposely"] != []]
print("All remove-purposely:", len(results))
results = [
    r for r in results
    if not any(
        re.search(
            f, 
            r["remove-purposely"][-1]["edit_meta_from"].get("comment", "").lower()
        ) for f in FILTERS
    )
]
print("All filtered", len(results))

with open(O_PATH, 'w') as f:
    json.dump(results, f)
