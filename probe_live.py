import json
import broken


QUEUE_PATH = "probe/probe_live/probe_live_scheduled.json"
O_FILE = "probe/probe_live/probe_live_results.json"
SHARD = 3
N_SHARD = 4

AZ_IPs_PATH = "/home/huanchen/azure-deploy/az-proxy/az_config/resource_ips.json"
PROXY_IPs = [v for _, v in json.load(open(AZ_IPs_PATH, 'r')).items()]
print(PROXY_IPs)
PROXY_IP = PROXY_IPs[SHARD]
broken.PROXIES = {
    "http": f"http://{PROXY_IP}:8888",
    "https": f"http://{PROXY_IP}:8888"
}
print(broken.PROXIES)

def process_queue(input_file, output_file, start_index=0):

    with open(input_file, "r", encoding="utf-8") as infile:
        probe_queue = json.load(infile)
    probe_queue = probe_queue[start_index::N_SHARD]

    for index in range(len(probe_queue)):
        try:
            entry = probe_queue[index]
            url = entry["url"]
            
            is_broken, reason = broken.broken(url)
            
            entry["is_broken"] = is_broken
            entry["reason"] = reason

            with open(output_file, "a", encoding="utf-8") as outfile:
                json.dump(entry, outfile)
                outfile.write("\n")

        except Exception as e:
            print(f"Error processing entry {index+1}: {e}", flush=True)

        print(f"Processed {index + 1}/{len(probe_queue)}: {url}", flush=True)
    print("Processing completed.")


if __name__ == "__main__":
    process_queue(QUEUE_PATH, O_FILE, SHARD)
