import xml.etree.ElementTree as ET
import json
import re
from datetime import datetime

# Function to clean and normalize article names (remove non-alphanumeric characters and spaces)
def normalize_article_name(article_name):
    return re.sub(r'\W+', '', article_name).replace(' ', '')

# Function to check if the link was augmented by archive.org or web.archive.org
def check_if_augmented(revision_text, broken_link):
    archive_pattern = re.compile(r'(https?://(web\.)?archive\.org/web/\d+/)' + re.escape(broken_link))
    return bool(archive_pattern.search(revision_text))

# Function to check if a username is a bot (if username ends with 'bot')
def is_bot_username(username):
    return username.lower().endswith('bot')

# Function to log results for each article to a txt file
def log_result_to_txt(output_file, article_data):
    with open(output_file, 'a+', encoding='utf-8') as outfile:
        json.dump(article_data, outfile, indent=4)
        outfile.write('\n')

def parse_history_dump(filename, broken_links_data, output_file, progress_log_file):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    
    current_article_title = None
    relevant_article = False  # Flag to track if the article is relevant (found in broken_links_data)

    for event, elem in context:
        tag_no_ns = elem.tag.split("}")[-1].lower().strip()

        # Capture the article title
        if event == "end" and tag_no_ns == "title":
            current_article_title = elem.text
            normalized_title = normalize_article_name(current_article_title)

            # Check if the title is in broken links data, set relevant_article flag accordingly
            if normalized_title in broken_links_data:
                relevant_article = True
                print(f"@@@{normalized_title}", flush=True)

                # Initialize the article data
                article_data = {
                    "dir": "edit_history_1",
                    "article_name": current_article_title,
                    "list_of_urls": []
                }

                # Initialize the dictionary for each broken link
                for broken_link in broken_links_data[normalized_title]["list_of_links"]:
                    article_data["list_of_urls"].append({
                        "url": broken_link,
                        "augmented": None,
                        "removed": None
                    })
            else:
                print(f"###{normalized_title}", flush=True)
                relevant_article = False  # Skip further processing for this article
                elem.clear()  # Clear title element immediately for irrelevant articles
                continue

        # Skip and clear elements for irrelevant articles
        if not relevant_article:
            # elem.clear()
            continue

        # Capture the article namespace
        if event == "end" and tag_no_ns == "ns":
            if elem.text != "0":  # Skip non-article pages
                current_article_title = None
                relevant_article = False
            elem.clear()  # Clear the namespace element after processing
            continue

        # Only process revisions if the article is relevant
        if event == "end" and tag_no_ns == "revision" and current_article_title:
            revision_timestamp = None
            contributor_name = None
            revision_meta = {"log": []}
            revision_dumped = False

            while True:
                event, elem = next(context)
                tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag

                if event == "end" and tag_no_ns == "timestamp":
                    timestamp = elem.text
                    elem.clear()  # Clear the timestamp element after processing

                    # Process only revisions from 2019 onwards
                    if timestamp[:4] >= "2019":
                        print(f"- -{timestamp}", flush=True)
                        while True:
                            event, elem = next(context)
                            tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                            if event == "end" and tag_no_ns == "username":
                                username = elem.text
                                revision_meta["log"].append({"timestamp": timestamp, "username": username})
                                elem.clear()  # Clear the username element after processing
                                break

                        print(f"\t\t{timestamp} {username}", flush=True)
                        # Capture revision text and process for broken links
                        if not revision_dumped:
                            revision_dumped = True
                            while True:
                                event, elem = next(context)
                                tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                                if event == "end" and tag_no_ns == "text":
                                    revision_text = elem.text or ''
                                    elem.clear()  # Clear the text element after processing
                                    break

                        # Process the broken links for augmentation/removal detection
                        for link_info in article_data["list_of_urls"]:
                            print(f"\t\t\t-{link_info['url']}", flush=True)
                            # Skip if both augmented and removed are already found
                            if link_info["augmented"] and link_info["removed"]:
                                continue

                            # Check if the broken link was removed
                            if not link_info["removed"] and link_info["url"] not in revision_text:
                                link_info["removed"] = {
                                    "remove_date": timestamp,
                                    "username": username,
                                    "is_bot": is_bot_username(username)
                                }

                            # Check if the broken link was augmented
                            if not link_info["augmented"] and check_if_augmented(revision_text, link_info["url"]):
                                link_info["augmented"] = {
                                    "augment_date": timestamp,
                                    "username": username,
                                    "is_bot": is_bot_username(username)
                                }

                            print(f"\t\t\t+{link_info['url']}", flush=True)

                    else:
                        elem.clear()

            elem.clear()  # Clear the revision element after processing

            # Write out the results for the current article
            log_result_to_txt(output_file, article_data)


# Load broken links data (only focusing on the ones in grouped_broken_links)
with open("grouped_broken_links.json", "r", encoding="utf-8") as file:
    broken_links_data = json.load(file)
    broken_links_data = broken_links_data["edit_history_1"]
print(list(broken_links_data))

# Parse the XML dump and log the results to a txt file
parse_history_dump("enwiki-latest-pages-meta-history1.xml-p10853p11410", broken_links_data, "broken_links_results.txt", "progress_log.txt")


"""
the function reads all edit histories in a specific dump
if the article does not appear in grouped_broken_links.json["edit_history_1"]: then skip this article totally
(continued)
if the article did apprear in the grouped_broken_links.json["edit_history_1"]: 
    1. first initialize a dictionary containing all links in the grouped_broken_links.json["edit_history_1"][article name] which includes
        {
            url:
            augmented: {
                date time of edition
                username
                is_bot (depending on if username ends with bot)
            }
            removed: {
                date time of edition
                username
                is_bot (depending on if username ends with bot)
            }
        }
    2. interate through all revisions:
        a. skip all revisions ealier than 2019 (focus on >= 2019)
        b. for each revision try to find if the links was removed or augmented (to find augmented, use your way of regex), note that you only
        need to update the augmented/removed when the entries are empty! and you may break the revision iteration as soon as the augmented and 
        removed are not empty
    3. write out to a txt file (different from the json file format that we've been using) with json objects dumped, the eventual dump per article should look like this
        {
            dir:
            article name:
            list of urls: [
                {
                    (the above ds)
                }
            ]
        }
"""