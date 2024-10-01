import xml.etree.ElementTree as ET
import json
import os


DIR = "./edit_history/"
if not os.path.exists(DIR):
    os.makedirs(DIR)

def parse_titles(filename):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)
    
    i = 0

    for event, elem in context:

        revision_meta = {}
        revision_text_2019 = ""

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
        print(title, flush=True)
        revision_meta["title"] = title

        revision_dumped = False

        revision_meta["log"] = []
        while True:
            event, elem = next(context)
            tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
            if event == "end" and tag_no_ns == "page":
                break
            if event == "end" and tag_no_ns == "timestamp":
                timestamp = elem.text
                print(timestamp, flush=True)
                while True:
                    event, elem = next(context)
                    tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                    if event == "end" and tag_no_ns == "username":
                        username = elem.text
                        print(username, flush=True)
                        revision_meta["log"].append({"timestamp": timestamp, "username": username})
                        break
                if not revision_dumped and timestamp[:4] == "2019":
                    revision_dumped = True
                    while True:
                        event, elem = next(context)
                        tag_no_ns = elem.tag.split("}")[1] if "}" in elem.tag else elem.tag
                        if event == "end" and tag_no_ns == "text":
                            print(elem.text, flush=True)
                            revision_text_2019 = elem.text
                            break
        elem.clear()

        with open(f"{DIR}{title}-meta.json", 'w') as f:
            json.dump(revision_meta, f)
        with open(f"{DIR}{title}-2019.txt", 'w') as f:
            f.write(revision_text_2019)
        print("------------------------------------------------", flush=True)

        i += 1
        if i == 5:
            break

archive_path = 'enwiki-latest-pages-meta-history1.xml-p10853p11410'
parse_titles(archive_path)
