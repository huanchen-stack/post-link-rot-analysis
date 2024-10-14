import xml.etree.ElementTree as ET
import json
import os
import traceback
# import gc
# from memory_profiler import profile


DUMP_PATH = "enwiki/enwiki-latest-pages-meta-history4.xml-p311330p316599"
DIR = "./edit_history/edit_history_4/"
REVISION_SAVE_YEAR = "2019"

if not os.path.exists(DIR):
    os.makedirs(DIR)

def get_tag_no_ns(elem):
    return elem.tag.split("}")[1] if "}" in elem.tag else elem.tag

def clean_title(title):
    return ''.join([c for c in title if c.isalnum()])

def iter_til_tag(context, tag_names, event_listen="end"):
    ret = None
    while True:
        event, elem = next(context)
        tag_no_ns = get_tag_no_ns(elem)
        if event == event_listen and tag_no_ns == "page":
            elem.clear()
            return "END!!!EXIT!!!"
        
        if event == "end" and tag_no_ns in tag_names:
            ret = elem.text
            elem.clear()
            break
    return ret

# @profile
def parse_titles(filename):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    
    i = 0
    for _, elem in context:
        title = ""
        try:
            revision_meta = {}
            revision_text_save = ""

            # Find title
            title = iter_til_tag(context, ["title"])

            # Check if ns==0 (main namespace)
            inner_ns = iter_til_tag(context, ["ns"])
            if inner_ns!= "0":
                continue
            
            # Store title in metadata
            revision_meta["title"] = title

            # Store article id (not revision id)
            revision_meta["article_id"] = iter_til_tag(context, ["id"])
            
            # Iterate through revisions
            revision_meta["revision"] = []
            revision_dumped = False

            while True:
                revision_id = iter_til_tag(context, ["id"])
                if revision_id == "END!!!EXIT!!!":
                    break

                timestamp = iter_til_tag(context, ["timestamp"])

                username = iter_til_tag(context, ["username", "ip"])

                revision_meta["revision"].append({
                    "id": revision_id,
                    "timestamp": timestamp,
                    "username": username
                })

                text = iter_til_tag(context, ["text"])
                text = text if text else ""
                if not revision_dumped and timestamp[:4] == REVISION_SAVE_YEAR:
                    revision_dumped = True
                    revision_text_save = text

                elem.clear()
            elem.clear()

            title_cleaned = clean_title(title)
            with open(f"{DIR}{title_cleaned}-meta.json", 'w', encoding='utf-8') as f:
                json.dump(revision_meta, f, indent=4)
            with open(f"{DIR}{title_cleaned}-2019.txt", 'w', encoding='utf-8') as f:
                f.write(revision_text_save)

        except Exception as e:
            traceback.print_exc()
            print(f"Error processing {i+1} {title}: {e}", flush=True)
            try:
                iter_til_tag(context, ["page"], event_listen="end")
            except Exception as e:
                print(f"Error skipping page: {e}", flush=True)
            try:
                iter_til_tag(context, ["page"], event_listen="start")
            except Exception as e:
                print(f"Error resuming page: {e}", flush=True)

        i += 1
        print(f"Processed {i} pages {title}", flush=True)
        # if i == 100:
        #     break


if __name__ == "__main__":
    parse_titles(DUMP_PATH)
