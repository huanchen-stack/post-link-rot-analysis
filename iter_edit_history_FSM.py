import xml.etree.ElementTree as ET
import json
import os
import traceback
import re
import fuzzy_match
import extract_links


SHARD = 0
ENWIKI_DUMPS = [
    "enwiki-latest-pages-meta-history1.xml-p10839p11398",
    "enwiki-latest-pages-meta-history2.xml-p102439p106234",
    "enwiki-latest-pages-meta-history3.xml-p151574p154328",
    "enwiki-latest-pages-meta-history4.xml-p311330p316599"
]
DUMP_PATH = f"enwiki/{ENWIKI_DUMPS[SHARD]}"
DIR = f"edit_history/edit_history_{SHARD+1}/"
ITER_DIR = "edit_history/iter/"
O_FNAME = "iter_edit_history_results.json"
REVISION_SAVE_YEAR = "2019"
CUR_YEAR = "2024"

os.makedirs(ITER_DIR, exist_ok=True)

def get_tag_no_ns(elem):
    return elem.tag.split("}")[1] if "}" in elem.tag else elem.tag

def clean_title(title):
    return ''.join([c for c in title if c.isalnum()])


def extract_marked_dead_citations(target_url, revision_text):
    escaped_url = re.escape(target_url)
    cite_dead_regex = rf"\{{\{{.*?cite.*?{escaped_url}.*?url-status\s*=\s*dead.*?\}}\}}"
    matches = re.findall(cite_dead_regex, revision_text, flags=re.IGNORECASE | re.DOTALL)
    return matches

with open(os.path.join(ITER_DIR, "probe_live_broken_links.json"), "r", encoding="utf-8") as file:
    ALL_BROKEN_LINKS = json.load(file)

def _page(event, elem, fsm):
    global ALL_BROKEN_LINKS

    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "title":
        title = elem.text
        sanitized_title = clean_title(title)
        folder_path = DIR.rstrip("/")
        if not sanitized_title in ALL_BROKEN_LINKS[folder_path]:
            fsm["state"] = "_skip"
            return
        
        meta_file_path = f"{DIR}{sanitized_title}-meta.json"
        with open(meta_file_path, "r") as meta_file:
            revisions = json.load(meta_file)["revisions"]
        if revisions == []:
            fsm["state"] = "_skip"
            return
        
        # no need to ensure both 2019 and 2024 are covered
        last_revision_timestamp = revisions[-1].get("timestamp", "")
        if last_revision_timestamp != "" and int(last_revision_timestamp[:4]) >= int(REVISION_SAVE_YEAR):
            fsm["revision-meta"] = {}
            fsm["first_revision_2019"] = {}
            for r in revisions:
                if "timestamp" not in r:
                    continue
                # if int(r["timestamp"][:4]) >= int(REVISION_SAVE_YEAR):
                if fsm["first_revision_2019"] == {}:
                    fsm["first_revision_2019"] = r
                fsm["revision-meta"][r["timestamp"]] = r
            fsm["last_revision"] = revisions[-1]
            fsm["broken_links"] = [
                link_obj for link_obj in ALL_BROKEN_LINKS[folder_path][sanitized_title]["list_of_links"]
            ]
            for link_obj in fsm["broken_links"]:
                link_obj["first_occurance"] = None
                link_obj["removal"] = []
                link_obj["augmentation"] = {
                    "edit_meta": None,
                    "augmentation_url": "",
                    "removal": []
                }
            fsm["arn_reference"] = json.load(open(f"{DIR}{sanitized_title}-arn.json", "r"))
        else:
            fsm["state"] = "_skip"
    elif event == "start" and tag_no_ns == "revision":
        fsm["state"] = "_revision"
    elif event == "end" and tag_no_ns == "page":
        if "broken_links" in fsm:
            # removal -> revert + purposely
            for link_obj in fsm["broken_links"]:
                link_obj["remove-revert"] = []
                link_obj["remove-purposely"] = []
                for removal in link_obj["removal"]:
                    if removal["consecutive_removal"] < 5:
                        link_obj["remove-revert"].append(removal)
                    else:
                        link_obj["remove-purposely"].append(removal)
                del link_obj["removal"]
            
                if "augmentation" in link_obj and "removal" in link_obj["augmentation"]:
                    link_obj["augmentation"]["remove-revert"] = []
                    link_obj["augmentation"]["remove-purposely"] = []
                    for removal in link_obj["augmentation"]["removal"]:
                        if removal["consecutive_removal"] < 5:
                            link_obj["augmentation"]["remove-revert"].append(removal)
                        else:
                            link_obj["augmentation"]["remove-purposely"].append(removal)
                    del link_obj["augmentation"]["removal"]

            write_results(fsm["broken_links"])

        for k in list(fsm):
            if k != "state":
                del fsm[k]
        fsm["state"] = "_page"
        # exit(0)

def _revision(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "timestamp":
        fsm["timestamp"] = elem.text
    elif event == "end" and tag_no_ns == "text":
        # if int(fsm["timestamp"][:4]) < int(REVISION_SAVE_YEAR):
        #     return
        revision_text = elem.text or ""
        # archived_links = extract_links.extract_external_links(revision_text)["archived_links"]
        try:
            for link_obj in fsm["broken_links"]:
                link_url = link_obj["url"]

                if link_obj["first_occurance"] is None:
                    if link_url in revision_text:
                        link_obj["first_occurance"] = fsm["revision-meta"][fsm["timestamp"]]
                    else:
                        continue
                # elif link_obj["mark_as_dead"] is None and link_url in fsm["arn_reference"] and fsm["arn_reference"][link_url]["last_revision_AUG_REM"]["type"] != "no_action":
                # # elif link_obj["mark_as_dead"] is None and link_url in revision_text:
                #     marked_dead_matches = extract_marked_dead_citations(link_url, revision_text)
                #     if marked_dead_matches and len(marked_dead_matches) > 0:
                #         link_obj["mark_as_dead"] = {
                #             "revision": fsm["revision-meta"][fsm["timestamp"]],
                #             "mark": marked_dead_matches[0] 
                #         }

                eventual_augmentation = ""
                if link_url in fsm["arn_reference"] and fsm["arn_reference"][link_url]["last_revision_AUG_REM"]["type"] == "augmented":
                    eventual_augmentation = fsm["arn_reference"][link_url]["last_revision_AUG_REM"]["match"]
                # eventual_removal = False
                # if link_url in fsm["arn_reference"] and fsm["arn_reference"][link_url]["last_revision_AUG_REM"]["type"] == "removed":
                #     eventual_removal = True

                if not fuzzy_match.check_if_removed(link_url, revision_text):
                    if link_obj["removal"] and link_obj["removal"][-1]["edit_meta_to"] is None:
                        link_obj["removal"][-1]["edit_meta_to"] = fsm["revision-meta"][fsm["timestamp"]]
                else:
                    if not link_obj["removal"] or link_obj["removal"][-1]["edit_meta_to"] is not None:
                        link_obj["removal"].append({
                            "consecutive_removal": 1,
                            "edit_meta_from": fsm["revision-meta"][fsm["timestamp"]],
                            "edit_meta_to": None
                        })
                    else:
                        link_obj["removal"][-1]["consecutive_removal"] += 1
                if link_obj["removal"]:
                    if fsm["timestamp"] == fsm["first_revision_2019"]["timestamp"]:
                        link_obj["removal"][-1]["first"] = True
                    if fsm["timestamp"] == fsm["last_revision"]["timestamp"]:
                        link_obj["removal"][-1]["last"] = True

                if fsm["timestamp"] == fsm["first_revision_2019"]["timestamp"]:    
                    if "==External links==" in revision_text and link_url in revision_text.split("==External links==")[1]:
                        link_obj["==External links=="] = True
                    else:
                        link_obj["==External links=="] = False

                if link_obj["augmentation"]["augmentation_url"] == "":
                    if eventual_augmentation != "" and eventual_augmentation in revision_text:
                        match = eventual_augmentation
                    else:
                        match = fuzzy_match.check_if_augmented_strict(link_url, revision_text)
                    if match != "":
                        link_obj["augmentation"]["edit_meta"] = fsm["revision-meta"][fsm["timestamp"]]
                        link_obj["augmentation"]["augmentation_url"] = match
                        if fsm["timestamp"] == fsm["first_revision_2019"]["timestamp"]:
                            link_obj["augmentation"]["first"] = True
                        if fsm["timestamp"] == fsm["last_revision"]["timestamp"]:
                            link_obj["augmentation"]["last"] = True

                aug_link_url = link_obj["augmentation"]["augmentation_url"]
                if aug_link_url != "":
                    if not fuzzy_match.check_if_removed(aug_link_url, revision_text):
                        if link_obj["augmentation"]["removal"] and link_obj["augmentation"]["removal"][-1]["edit_meta_to"] is None:
                            link_obj["augmentation"]["removal"][-1]["edit_meta_to"] = fsm["revision-meta"][fsm["timestamp"]]
                    else:
                        if not link_obj["augmentation"]["removal"] or link_obj["augmentation"]["removal"][-1]["edit_meta_to"] is not None:
                            link_obj["augmentation"]["removal"].append({
                                "consecutive_removal": 1,
                                "last": False,
                                "edit_meta_from": fsm["revision-meta"][fsm["timestamp"]],
                                "edit_meta_to": None
                            })
                        else:
                            link_obj["augmentation"]["removal"][-1]["consecutive_removal"] += 1
                    if link_obj["augmentation"]["removal"]:
                        if fsm["timestamp"] == fsm["first_revision_2019"]["timestamp"]:
                            link_obj["augmentation"]["removal"][-1]["first"] = True
                        if fsm["timestamp"] == fsm["last_revision"]["timestamp"]:
                            link_obj["augmentation"]["removal"][-1]["last"] = True
        except Exception as e:
            print(f"Error occurred: {e}")
            traceback.print_exc()
            fsm["state"] = "_skip"
    elif event == "end" and tag_no_ns == "revision":
        fsm["state"] = "_page"

def _skip(event, elem, fsm):
    tag_no_ns = get_tag_no_ns(elem)
    if event == "end" and tag_no_ns == "page":
        for k in list(fsm):
            if k != "state":
                del fsm[k]
        fsm["state"] = "_page"

# FSM dictionary for state transitions
state_functions = {
    "_page": _page,
    "_revision": _revision,
    "_skip": _skip
}

# Function to write results to a JSON file
def write_results(link_objects):
    with open(f"{ITER_DIR}/{O_FNAME}", 'a', encoding='utf-8') as f:
        for link_obj in link_objects:
            f.write(f"{json.dumps(link_obj)}\n")
    print(f"Logging results from folder {link_obj['folder_path']} article {link_obj['article_name']}", flush=True)
    # exit(0)

def parse_FSM(filename):
    context = ET.iterparse(filename, events=("start", "end"))
    context = iter(context)

    fsm = {
        "state": "_page",
    }
    for event, elem in context:
        state_func = state_functions.get(fsm["state"])
        state_func(event, elem, fsm)
        if event == "end":
            elem.clear()

if __name__ == "__main__":
    try:
        parse_FSM(DUMP_PATH)
    except Exception as e:
        print(f"Error occurred: {e}")
        traceback.print_exc()



"""
The above is the code you need to modify. Below are the instructions:
In this read of edit history, you come with a mission of seeing how broken links evolve throught edit histories.
When iterating through the edit history, you can use a finite state machine as well, but there won't be as many states as before.
Before iteration you need to load a js containing broke links: all_broken = edit_history/iter/grouped_broken_links.json

States;
1. _page:
you start with this state by default;
in the same way you look for </title> and extract the title, after you get the title, do the following:
- Check if the article is in all_broken[folder_path], otherwise go to _skip
- If it is, load another file that contains the meta data of the article in the same directory named as {sanitized title}-meta.json, load the file as revision-meta; otherwise go to _skip
- If the latest edit datetime is not in 2024, go to _skip

Initialize a page object as a list of link objects, each link objects; the link objects is from all_broken[folder_path][sanitized title]; you inherit all the old link attributes but add two more attributes:
- removal: []
- augmentation: {
    edit_meta: None, <- this will be filled by the -meta file's entry
    augmentation_url: "" <- this is to be filled once an augment is found
    removal: []
}
each removal object to be added to the removal links looks like this:
{
    consecutive_removal: 0, <- this will be incremented by 1 for each consecutive removal
    last: False, <- this will be set to True if the link does not appear in the very last revision in -meta file
    edit_meta_from: None, <- this will be filled by the -meta file's entry
    edit_meta_to: None, <- this will be filled by the -meta file's entry
}

same as before, go to revision state when you find <revision> tag;
same as before, go to _page state with </page> tag; however this time the hooking function is to append all links to edit_history/iter/results.json one by one

2. _revision:
not as before you need to handle that many details, this time you only need to extract the datetime and the text; so as usual, you look for </timestamp> and you look for </text>; same as before, if you cannot find </text>, use ""; however you need to perform the following actions:
(refer to this logic as the ground truth way, but read the FSM of link in the later paragraph for implementations)
- for each of the link object in the page object:
 - check if the link can be found in text
  - if the link can be found in text:
   - if the link's removal list is empty or the last object's edit_mata_to is not None: you don't need to do anything;
   - else: this means that the last object exists and the edit_meta_to is None, you need to fill the edit_meta_to with the meta entry from -meta of the corresponding datetime
  - else:
    - this means the link cannot be found in text, now see if there are no objects in the removal list OR the last removal object has a non-empty edit_meta_to, if so, you need to add a new removal object to the removal list with a meta entry from the -meta file of the corresponding datetime
    - else, this means that the last removal object has an empty edit_meta_to, you need to increment the consecutive_removal by 1
- for each link of the link object in the page object -> augmentation -> augmentation_url, if theses url exists do the same as above, the list is instead augmentation -> removal list

think of each link as a FSM, each link include the following states:
- link exists;  <- this is always the starting state
- link doesn't exist;
the transitions
- exists -> exists: do nothing
- exists -> doesn't exists: add edit_meta_from to removal list, you may need to create a new object
- doesn't exists -> exists: add edit_meta_to to removal list, you don't need to create an object
- doesn't exists -> doesn't exists: increment consecutive_removal by 1
for all transitions you need to do a -meta lookup and tell if this is the last edit
if the removal list is not empty, you need to add the last to the last object in the removal list

same as above you see </revision> you go to <page> state

3. _skip:

this is simpler, same as before, you only need to go to <page> state when you find </page> tag and do the default initializations

"""