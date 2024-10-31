import xml.etree.ElementTree as ET
import json
import os
import traceback

SHARD = 1
ENWIKI_DUMPS = [
    "enwiki-latest-pages-meta-history1.xml-p10839p11398",
    "enwiki-latest-pages-meta-history2.xml-p102439p106234",
    "enwiki-latest-pages-meta-history3.xml-p151574p154328",
    "enwiki-latest-pages-meta-history4.xml-p311330p316599"
]
DUMP_PATH = f"enwiki/{ENWIKI_DUMPS[SHARD]}"
DIR = f"edit_history/edit_history_{SHARD+1}/"
REVISION_SAVE_YEAR = "2019"

os.makedirs(DIR, exist_ok=True)

# Helper functions
def get_tag_no_ns(elem):
    return elem.tag.split("}")[1] if "}" in elem.tag else elem.tag

def clean_title(title):
    return ''.join([c for c in title if c.isalnum()])

# FSM function to process page state
def _page(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "title":
        fsm["page"]["title"] = elem.text
    elif event == "end" and tag_no_ns == "ns":
        fsm["page"]["ns"] = elem.text
        if elem.text != "0":
            fsm["state"] = "_skip"  # Skip non-article pages
    elif event == "end" and tag_no_ns == "id":
        fsm["page"]["id"] = elem.text
    elif event == "start" and tag_no_ns == "revision":
        fsm["revision"] = {}
        fsm["state"] = "_revision"  # Transition to in_revision
    elif event == "end" and tag_no_ns == "page":
        # Write page data to files
        write_page_data(fsm["page"], fsm["revision_list"], fsm["text_revision_save_year"]["text"], fsm["text"])
        # Re-initialize for the next page
        fsm["page"] = {}
        fsm["text_revision_save_year"] = {}
        fsm["revision_list"] = []
        fsm["revision"] = {}

# FSM function to process revision state
def _revision(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "id":
        fsm["revision"]["id"] = elem.text
    elif event == "end" and tag_no_ns == "timestamp":
        fsm["revision"]["timestamp"] = elem.text
    elif event == "start" and tag_no_ns == "contributor":
        fsm["state"] = "_contributor"  # Go to contributor state
    elif event == "end" and tag_no_ns == "comment":
        fsm["revision"]["comment"] = elem.text
    elif event == "end" and tag_no_ns == "text":
        if "timestamp" not in fsm["text_revision_save_year"] or int(fsm["revision"]["timestamp"][:4]) < int(REVISION_SAVE_YEAR):
            fsm["text_revision_save_year"]["text"] = elem.text or ""
            fsm["text_revision_save_year"]["timestamp"] = fsm["revision"]["timestamp"]
        fsm["text"] = elem.text or ""
    elif event == "end" and tag_no_ns == "revision":
        # Save revision and go back to page state
        fsm["revision_list"].append(fsm["revision"])
        fsm["state"] = "_page"

# FSM function to process contributor state
def _contributor(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "username":
        fsm["revision"]["username"] = elem.text
    elif event == "end" and tag_no_ns == "id":
        fsm["revision"]["contributor_id"] = elem.text
    elif event == "end" and tag_no_ns == "ip":
        fsm["revision"]["ip"] = elem.text
    elif event == "end" and tag_no_ns == "contributor":
        fsm["state"] = "_revision"  # Go back to in_revision

# FSM function to skip non-article pages
TOTAL_SKIPPED = 0
def _skip(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "page":
        global TOTAL_SKIPPED
        TOTAL_SKIPPED += 1
        # Reset to initial state
        fsm["page"] = {}
        fsm["text_revision_save_year"] = {}
        fsm["revision_list"] = []
        fsm["state"] = "_page"

# FSM dictionary for state transitions
state_functions = {
    "_page": _page,
    "_revision": _revision,
    "_contributor": _contributor,
    "_skip": _skip
}

# Function to write page data to files
TOTAL_COUNT = 0
COUNT_2019 = 0
COUNT_last = 0
def write_page_data(page_object, revision_list, text_revision_save_year, text_last_revision):
    title_cleaned = clean_title(page_object["title"])

    with open(f"{DIR}{title_cleaned}-meta.json", 'w', encoding='utf-8') as f:
        json.dump({
            "title": page_object["title"],
            "id": page_object["id"],
            "revisions": revision_list
        }, f, indent=4)

    global COUNT_2019, COUNT_last
    if text_revision_save_year:
        with open(f"{DIR}{title_cleaned}-2019.txt", 'w', encoding='utf-8') as f:
            f.write(text_revision_save_year)
            COUNT_2019 += 1
        if text_last_revision:
            with open(f"{DIR}{title_cleaned}-last.txt", 'w', encoding='utf-8') as f:
                f.write(text_last_revision)
                COUNT_last += 1

    global TOTAL_COUNT
    TOTAL_COUNT += 1
    print(f"Processed {TOTAL_COUNT} pages; writing {title_cleaned} files", flush=True)

def parse_FSM(filename):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)

    fsm = {
        "state": "_page",  # Initial state
        "page": {},
        "revision_list": [],
        "text_revision_save_year": {}
    }

    for event, elem in context:
        # print(event, elem.tag, flush=True)
        state_func = state_functions.get(fsm["state"])
        # print(state_func.__name__, flush=True)
        state_func(event, elem, fsm)
        if event == "end":
            elem.clear()

if __name__ == "__main__":
    try:
        parse_FSM(DUMP_PATH)
    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()

    print(TOTAL_COUNT, TOTAL_SKIPPED, TOTAL_COUNT+TOTAL_SKIPPED)
    print(COUNT_2019, COUNT_last)