import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime


DIR = "edit_history_1"
DUMP = "enwiki-latest-pages-meta-history1.xml-p10853p11410"
OFILE = "iter_edit_history_results_singlenohup_1.json"

def normalize_article_name(article_name):
    return re.sub(r'\W+', '', article_name).replace(' ', '')

def check_if_augmented(revision_text, broken_link):
    archive_pattern = re.compile(r'(https?://(web\.)?archive\.org/web/\d+/)' + re.escape(broken_link))
    return bool(archive_pattern.search(revision_text))

def is_bot_username(username):
    return username.lower().endswith('bot')

# NUM_LOGS = 10
def log_result_to_txt(output_file, article_data):
    # global NUM_LOGS
    with open(output_file, 'a+', encoding='utf-8') as outfile:
        outfile.write(f"{json.dumps(article_data)}\n")
    # NUM_LOGS -= 1
    # if NUM_LOGS == 0:
    #     exit(0)

def get_stats(list_of_urls):
    augmented_count = 0
    augmented_by_bot_count = 0
    removed_count = 0
    removed_by_bot_count = 0
    for url in list_of_urls:
        if url["augmented"]:
            augmented_count += 1
            if url["augmented"]["is_bot"]:
                augmented_by_bot_count += 1
        if url["removed"]:
            removed_count += 1
            if url["removed"]["is_bot"]:
                removed_by_bot_count += 1
    return {
        "total": len(list_of_urls),
        "augmented": augmented_count,
        "augmented_by_bot": augmented_by_bot_count,
        "removed": removed_count,
        "removed_by_bot": removed_by_bot_count
    }

def parse_history_dump(filename, broken_links_data, output_file):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)

    for event, elem in context:
        try:
            tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            tag_no_ns = tag_no_ns.lower().strip()
            if not (event == "end" and tag_no_ns == "title"):
                continue
            title = elem.text
            event, elem = next(context)
            tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            inner_ns = elem.text.strip()
            if inner_ns != '0':
                continue

            normalized_title = normalize_article_name(title)
            if normalized_title not in broken_links_data:
                continue
            print(f"@@@{normalized_title}", flush=True)

            broken_links_edit_history = {
                "dir": DIR,
                "article": title,
                "list_of_urls": [
                    {
                        "url": url,
                        "augmented": None,
                        "removed": None
                    } for url in broken_links_data[normalized_title]["list_of_links"]
                ]
            }

            while True:
                event, elem = next(context)
                tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                if event == "end" and tag_no_ns == "page":
                    break

                if event == "end" and tag_no_ns == "timestamp":
                    timestamp = elem.text
                    while True:
                        event, elem = next(context)
                        tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                        if event == "end" and tag_no_ns == "username":
                            username = elem.text
                            break
                    # print(timestamp, username, flush=True)
                
                    if int(timestamp[:4]) >= 2019:
                        while True:
                            event, elem = next(context)
                            tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                            if event == "end" and tag_no_ns == "text":
                                revision_text = elem.text
                                break

                        for link in broken_links_edit_history["list_of_urls"]:
                            if not link["augmented"]:
                                if check_if_augmented(revision_text, link["url"]):
                                    link["augmented"] = {}
                                    link["augmented"]["timestamp"] = timestamp
                                    link["augmented"]["username"] = username
                                    link["augmented"]["is_bot"] = is_bot_username(username)
                            if not link["removed"]:
                                if link["url"] not in revision_text:
                                    link["removed"] = {}
                                    link["removed"]["timestamp"] = timestamp
                                    link["removed"]["username"] = username
                                    link["removed"]["is_bot"] = is_bot_username(username)

            broken_links_edit_history["stats"] = get_stats(broken_links_edit_history["list_of_urls"])
            log_result_to_txt(output_file, broken_links_edit_history)

        except Exception as e:
            print("====================================", flush=True)
            print(e, flush=True)


def driver():
    with open("grouped_broken_links.json", "r", encoding="utf-8") as file:
        broken_links_data = json.load(file)
    broken_links_data = broken_links_data[DIR]

    parse_history_dump(DUMP, broken_links_data, OFILE)


if __name__ == "__main__":
    driver()