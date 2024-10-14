import json
import broken


WRONG_RESULTS_FILE = "probe/probe_live/probe_live_results.json"
PATCHED_O_FILE = "probe/probe_live/probe_live_results_patched.json"
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
        mixed_results = [json.loads(line.strip()) for line in infile.readlines()]
    mixed_results = mixed_results[start_index::N_SHARD]
    mixed_results = mixed_results[5000:]
    # to sanitize the rest, mixed_results = mixed_results[5000:]

    i = 0
    for result in mixed_results:
        if result["is_broken"] and result["reason"] == "Page Parked":
            is_broken, reason = broken.broken(result["url"])
            result["is_broken"] = is_broken
            result["reason"] = reason
            print(f"FIXING {result['url']} (Page Parked) to {result['reason']}... {is_broken}... done", flush=True)
        with open(output_file, "a", encoding="utf-8") as outfile:
            outfile.write(f"{json.dumps(result)}\n")
        i += 1
        print(f"Sanitizing and fixing {i}/{len(mixed_results)}: {result['url']}", flush=True)
    print("Sanitization and fixing completed.")


if __name__ == "__main__":
    process_queue(WRONG_RESULTS_FILE, PATCHED_O_FILE, SHARD)
