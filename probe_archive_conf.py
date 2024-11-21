import requests
import json
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta
import re


AZ_IPs_PATH = "/home/huanchen/azure-deploy/az-proxy/az_config/resource_ips.json"
PROXY_IPs = [v for _, v in json.load(open(AZ_IPs_PATH, 'r')).items()]
print(PROXY_IPs, flush=True)

QUEUE_PATH = "probe/probe_archive/probe_archive_scheduled.json"
O_PATH = "probe/probe_archive/probe_archive_results_conf.json"

SHARD = 5
N_SHARD = 8
PROXY_IP = PROXY_IPs[SHARD]
PROXIES = {
    "http": f"http://{PROXY_IP}:8888",
    "https": f"http://{PROXY_IP}:8888"
}

USER_AGENT = "curl"
FMT = "%Y%m%d%H%M%S"

def is_homepage(url):
    parsed_url = urlparse(url)
    path = parsed_url.path.rstrip('/').lower()
    homepage_paths = {
        '', '/index', '/index.html', '/index.htm',
        '/home', '/home.html', '/home.htm',
        '/default', '/default.html', '/default.htm',
        '/main', '/main.html', '/main.htm',
        '/welcome', '/welcome.html', '/welcome.htm',
        '/start', '/start.html', '/start.htm',
        '/landing', '/landing.html', '/landing.htm',
        '/login', '/login.html', '/login.htm',
        '/signin', '/signin.html', '/signin.htm',
        '/signup', '/signup.html', '/signup.htm',
        '/about', '/about.html', '/about.htm',
    }
    return path in homepage_paths


def extract_original_url(wayback_url):    
    pattern = r"https?://web\.archive\.org/web/\d+/(http[s]?://.+)"
    return re.match(pattern, wayback_url).group(1)


# Example usage
wayback_url = "https://web.archive.org/web/20210814081209/http://www.racingcampbells.com/content/campbell.archives/bonneville.400-just.for.the.record.html"
original_url = extract_original_url(wayback_url)
if original_url:
    print(f"Original URL: {original_url}")
else:
    print("No original URL found.")


def probe_wayback_historical_status(url, timestamp):
    queries = []
    closest_prev_status, closest_next_status = None, None

    ts_edit = ''.join(c for c in timestamp if c.isdigit())
    dt_edit = datetime.strptime(ts_edit, FMT)

    ts_closest_prev, url_closest_prev = None, None
    ts_closest_next, url_closest_next = None, None


    dt_n_days_prior = dt_edit - timedelta(days=180)
    ts_n_days_prior = dt_n_days_prior.strftime(FMT)
    cdx_query_closest_prev = f"http://web.archive.org/cdx/search/cdx?url={url}&from={ts_n_days_prior}&to={ts_edit}"
    try:
        print("\t", cdx_query_closest_prev, flush=True)
        response = requests.get(cdx_query_closest_prev, headers={"User-Agent": USER_AGENT}, proxies=PROXIES, timeout=60)
        queries.append(cdx_query_closest_prev)
        time.sleep(10)
        ts_closest_prev, url_closest_prev = response.text.strip().split("\n")[-1].split()[1:3]
    except:
        closest_prev_status = "Not captured or Captures too far"

    if ts_closest_prev and not closest_prev_status:
        wayback_query_closest_prev = f"https://web.archive.org/web/{ts_closest_prev}/{url_closest_prev}"
        print("\t", wayback_query_closest_prev, flush=True)
        response = requests.get(wayback_query_closest_prev, headers={"User-Agent": USER_AGENT}, proxies=PROXIES)
        queries.append(wayback_query_closest_prev)
        time.sleep(10)
        closest_prev_status = str(response.status_code)
        if response.status_code == 200:
            wayback_final_original_url = extract_original_url(response.url)
            if not is_homepage(url) and is_homepage(wayback_final_original_url):
                closest_prev_status = "Soft 404"

    cdx_query_closest_next = f"http://web.archive.org/cdx/search/cdx?url={url}&from={ts_edit}&limit=1"
    try:
        print("\t", cdx_query_closest_next, flush=True)
        response = requests.get(cdx_query_closest_next, headers={"User-Agent": "curl"}, proxies=PROXIES)
        queries.append(cdx_query_closest_next)
        time.sleep(10)
        ts_closest_next, url_closest_next = response.text.strip().split("\n")[0].split()[1:3]
        if abs(datetime.strptime(ts_closest_next, FMT) - datetime.strptime(ts_edit, FMT)).days > 180:
            closest_next_status = "Captures too far"
    except:
        closest_next_status = "Not captured"

    if ts_closest_next and not closest_next_status:
        wayback_query_closest_next = f"https://web.archive.org/web/{ts_closest_next}/{url_closest_next}"
        print("\t", wayback_query_closest_next, flush=True)
        response = requests.get(wayback_query_closest_next, headers={"User-Agent": "curl"}, proxies=PROXIES)
        queries.append(wayback_query_closest_next)
        time.sleep(10)
        closest_next_status = str(response.status_code)
        if response.status_code == 200:
            wayback_final_original_url = extract_original_url(response.url)
            if not is_homepage(url) and is_homepage(wayback_final_original_url):
                closest_prev_status = "Soft 404"

    if closest_prev_status[0] in ['4', '5', '6', 'S'] and closest_next_status[0] in ['4', '5', '6', 'S']:
        category = "Dead"
    elif closest_prev_status[0] == '2' and closest_next_status[0] == '2':
        category = "Alive"
    elif closest_prev_status[0] in ['N', 'C'] and closest_next_status[0] in ['N', 'C']:
        category = "No Confidence"
    elif closest_prev_status[0] in ['N', 'C'] and closest_next_status[0] in ['4', '5', '6', 'S']:
        category = "Low Confidence Dead"
    elif closest_prev_status[0] in ['4', '5', '6', 'S'] and closest_next_status[0] in ['N', 'C']:
        category = "Low Confidence Dead"
    elif closest_prev_status[0] in ['N', 'C'] and closest_next_status[0] == '2':
        category = "Low Confidence Alive"
    elif closest_prev_status[0] == '2' and closest_next_status[0] in ['N', 'C']:
        category = "Low Confidence Alive"
    else:
        category = "Inconsistent"

    log = {
        "category": category,
        "ts_edit": ts_edit,
    }
    if ts_closest_prev:
        log["ts_closest_prev"] = ts_closest_prev
        log["closest_prev_status"] = closest_prev_status
    if ts_closest_next:
        log["ts_closest_next"] = ts_closest_next
        log["closest_next_status"] = closest_next_status
    log["queries"] = queries
    return log

WAYBACK_PROBE_LOG = {}
def process_queue(input_file, output_file, start_index=0):
    global WAYBACK_PROBE_LOG

    with open(input_file, "r", encoding="utf-8") as infile:
        probe_queue = json.load(infile)
    # probe_queue = probe_queue[:16]
    probe_queue = probe_queue[start_index::N_SHARD]

    for index in range(len(probe_queue)):
        try:
            entry = probe_queue[index]
            entry["wayback_historical_status"] = probe_wayback_historical_status(
                entry["url"], 
                entry["remove-purposely"][-1]["edit_meta_from"]["timestamp"]
            )

            if entry["wayback_historical_status"]["category"] not in WAYBACK_PROBE_LOG:
                WAYBACK_PROBE_LOG[entry["wayback_historical_status"]["category"]] = 0
            WAYBACK_PROBE_LOG[entry["wayback_historical_status"]["category"]] += 1

            with open(output_file, "a", encoding="utf-8") as outfile:
                json.dump(entry, outfile)
                outfile.write("\n")

        except Exception as e:
            print(f"Error processing entry {index+1}: {e}", flush=True)

        print(f"Processed {index + 1}/{len(probe_queue)}... {WAYBACK_PROBE_LOG} [url]: {entry['url']}", flush=True)
    print("Processing completed.")

process_queue(QUEUE_PATH, O_PATH, SHARD)
