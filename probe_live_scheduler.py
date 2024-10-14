import json
import random

MERGED_BY_HOST_FILE = "probe/probe_live/merged_live_links_by_host.json"
O_FILE = "probe/probe_live/probe_live_scheduled.json"

def schedule_links(merged_by_host_file, o_file):
    with open(merged_by_host_file, 'r') as f:
        merged_by_host = json.load(f)

    scheduled_links = []
    for _, d_ in merged_by_host.items():
        scheduled_links += random.sample(d_["live_links"], min(len(d_["live_links"]), 50))

    random.shuffle(scheduled_links)

    with open(o_file, 'w') as f:
        json.dump(scheduled_links, f, indent=4)

    print(f"Scheduled {len(scheduled_links)} live links to {o_file}")


if __name__ == "__main__":
    schedule_links(MERGED_BY_HOST_FILE, O_FILE)