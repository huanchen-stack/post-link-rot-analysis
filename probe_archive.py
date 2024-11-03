import requests
import json
from urllib.parse import urlparse, urlunparse
import time


AZ_IPs_PATH = "/home/huanchen/azure-deploy/az-proxy/az_config/resource_ips.json"
PROXY_IPs = [v for _, v in json.load(open(AZ_IPs_PATH, 'r')).items()]
print(PROXY_IPs)

QUEUE_PATH = "probe/probe_archive/probe_archive_scheduled.json"
O_PATH = "probe/probe_archive/probe_archive_results.json"

SHARD = 3
N_SHARD = 4
PROXY_IP = PROXY_IPs[SHARD]
PROXIES = {
    "http": f"http://{PROXY_IP}:8888",
    "https": f"http://{PROXY_IP}:8888"
}

def get_wayback_cdx_query(url, _from, _to, statuscode, limit=1):
    query_url = "http://web.archive.org/cdx/search/cdx?"
    
    parsed = urlparse(url)
    parsed_path_listed = parsed.path.rstrip('/').split('/')
    look_for_siblings = False
    if len(parsed_path_listed) > 2:
        look_for_siblings = True
        parent_path = '/'.join(parsed_path_listed[:-1])
        parent_url = urlunparse(parsed._replace(path=parent_path, query='', fragment=''))
    if look_for_siblings:
        query_url += f"url={parent_url}/*"
    else:
        query_url += f"url={url}"

    query_url += f"&from={_from}&to={_to}"
    query_url += f"&limit={limit}"
    query_url += f"&filter=statuscode:{str(statuscode)[0]}"
    
    if look_for_siblings:
        query_url += "&filter=!original:{parent_url}" # exclude parent dir
    # query_url += "&filter=mimetype:application/" if "pdf" in url else "&filter=mimetype:text/html" # ?????
    # query_url += "&output=json"

    return query_url, look_for_siblings

def is_wayback_historically_alive(url, timestamp):
    ts_from = ''.join(c for c in timestamp if c.isdigit())
    ts_to = str(int(timestamp[:4])+1)
    query_url, sibling = get_wayback_cdx_query(
        url, 
        _from=ts_from, 
        _to=ts_to,
        statuscode=200,
    )
    log = {
        "type": "",
        "sibling": sibling,
        "ts_from": ts_from,
        "ts_to": ts_to,
    }
    response = requests.get(query_url, headers={"User-Agent": "curl"}, proxies=PROXIES)
    time.sleep(10)
    if response.text != "":
        log["type"] = "200 OK directly"
        return True, log

    query_url, _ = get_wayback_cdx_query(
        url, 
        _from=ts_from, 
        _to=ts_to,
        statuscode=300,
        limit=10,
    )
    response = requests.get(query_url, headers={"User-Agent": "curl"}, proxies=PROXIES)
    time.sleep(10)
    if response.text!= "":
        paths_to_check = set()
        entries_to_check = response.text.strip().split("\n")
        for entry in entries_to_check:
            url_to_check = entry.split()[2]
            paths_to_check.add(urlparse(url_to_check).path)
            timestamp_to_check = entry.split()[1]
            follow_redir_query = f"https://web.archive.org/web/{timestamp_to_check}/{url_to_check}"

            response = requests.get(follow_redir_query, headers={"User-Agent": "curl"}, proxies=PROXIES)
            time.sleep(10)
            if response.status_code == 200:
                log["type"] = "200 OK as REDIRECTION destination"
                return True, log

            if len(paths_to_check) > 3:
                break
    
    log["type"] = "No 200 OK or 3xx REDIRECTION found"
    return False, log

# r = is_wayback_historically_alive("http://english.farsnews.com/newstext.aspx", "20190101045757")
# print(r)
# exit(0)

WAYBACK_SAME_DIR_ALIVE = 0
WAYBACK_SAME_DIR_DEAD = 0
def process_queue(input_file, output_file, start_index=0):
    global WAYBACK_SAME_DIR_ALIVE, WAYBACK_SAME_DIR_DEAD

    with open(input_file, "r", encoding="utf-8") as infile:
        probe_queue = json.load(infile)
    probe_queue = probe_queue[start_index::N_SHARD]

    for index in range(len(probe_queue)):
        try:
            entry = probe_queue[index]
            wayback_historically_alive, reason = is_wayback_historically_alive(
                entry["url"], 
                entry["remove-purposely"][-1]["edit_meta_from"]["timestamp"]
            )
            entry["wayback_historically_alive"] = [wayback_historically_alive, reason]

            if entry["wayback_same_dir_alive"]:
                WAYBACK_SAME_DIR_ALIVE += 1
            else:
                WAYBACK_SAME_DIR_DEAD += 1

            with open(output_file, "a", encoding="utf-8") as outfile:
                json.dump(entry, outfile)
                outfile.write("\n")

        except Exception as e:
            print(f"Error processing entry {index+1}: {e}", flush=True)

        print(f"Processed {index + 1}/{len(probe_queue)}... wayback_same_dir[_alive({WAYBACK_SAME_DIR_ALIVE}) _dead ({WAYBACK_SAME_DIR_DEAD})] [url]: {entry['url']}", flush=True)
    print("Processing completed.")

process_queue(QUEUE_PATH, O_PATH, SHARD)
