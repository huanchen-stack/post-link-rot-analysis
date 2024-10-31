import json


RESULTS_PATH = "edit_history/iter/results.json"


with open(RESULTS_PATH, 'r') as f:
    all_results = [json.loads(d.strip()) for d in f.readlines()]

BOT_KEYWORDS = [
    "bot", "script", "wp:", "ng", "auto", "maintenance tag update", "awb", "mos", "assist"
]

def is_bot(text):
    global BOT_KEYWORDS

    text = text.lower()
    for keyword in BOT_KEYWORDS:
        if keyword in text:
            return True
    return False

STATS = {
    "total_count": 0,
    "no-actions": {
        "count": 0
    },  # key is reason for broken; value is count
    "augmented_already": {
        "count": 0,
        "aug-removed": 0
    },
    "augmented": {
        "count": 0,
        "bot": 0,
        "human": 0,
        "mixed": 0,
        "aug-removed": 0
    },
    "remove-revert": {
        "link-count": 0,
        "occurance-count": 0,
        "bot": 0,
        "human": 0,
        "mixed": 0
    },
    "remove-purposely": {
        "count": 0,
        "==External links==": 0,
        # "content": 0,  # store to edit_history/iter/remove_purposely_content.json
        # "format": 0,   # store to edit_history/iter/remove_purposely_format.json
        # "link-rot": {  # store to edit_history/iter/remove_purposely_link_rot.json
        #     "==External links==": 0,
        #     "other": 0
        # }
    }
}
with open("edit_history/iter/_no_actions.json", "w") as f:
    pass

with open("edit_history/iter/_augmentation_by_mixed.json", "w") as f:
    pass

with open("edit_history/iter/_augmentation_by_human.json", "w") as f:
    pass

with open("edit_history/iter/_remove_purposely.json", "w") as f:
    pass

for link_obj in all_results:
    try:
        STATS["total_count"] += 1
        if link_obj["augmentation"]["augmentation_url"] == "" and link_obj["remove-purposely"] == []:
            if type(link_obj["reason"]) == list:
                reason = link_obj["reason"][0]
            else:
                reason = link_obj["reason"]
            STATS["no-actions"][reason] = STATS["no-actions"].get(reason, 0) + 1
            STATS["no-actions"]["count"] += 1
            with open("edit_history/iter/_no_actions.json", "a") as f:
                f.write(f"{json.dumps(link_obj)}\n")

        if link_obj["augmentation"]["augmentation_url"] != "" and link_obj["augmentation"].get("first", False):
            STATS["augmented_already"]["count"] += 1
            if link_obj["augmentation"]["remove-purposely"] != [] and link_obj["augmentation"]["remove-purposely"][-1]["edit_meta_to"] is None:
                STATS["augmented_already"]["aug-removed"] += 1

        if link_obj["augmentation"]["augmentation_url"] != "" and not link_obj["augmentation"].get("first", False):
            if is_bot(link_obj["augmentation"]["edit_meta"].get("username", "")):
                STATS["augmented"]["bot"] += 1
            elif is_bot(link_obj["augmentation"]["edit_meta"].get("comment", "")):
                STATS["augmented"]["mixed"] += 1
                with open("edit_history/iter/_augmentation_by_mixed.json", "a") as f:
                    f.write(f"{json.dumps(link_obj)}\n")
            else:
                STATS["augmented"]["human"] += 1
                with open("edit_history/iter/_augmentation_by_human.json", "a") as f:
                    f.write(f"{json.dumps(link_obj)}\n")
            STATS["augmented"]["count"] += 1
            if link_obj["augmentation"]["remove-purposely"]!= [] and link_obj["augmentation"]["remove-purposely"][-1]["edit_meta_to"] is None:
                STATS["augmented"]["aug-removed"] += 1

        if link_obj["remove-revert"] != []:
            for rev_obj in link_obj["remove-revert"]:
                STATS["remove-revert"]["occurance-count"] += 1
                if is_bot(rev_obj["edit_meta_to"].get("username", "")):
                    STATS["remove-revert"]["bot"] += 1
                elif is_bot(rev_obj["edit_meta_to"].get("comment", "")):
                    STATS["remove-revert"]["mixed"] += 1
                else:
                    STATS["remove-revert"]["human"] += 1
            STATS["remove-revert"]["link-count"] += 1

        if link_obj["remove-purposely"] != []:
            STATS["remove-purposely"]["count"] += 1
            if link_obj["==External links=="]:
                STATS["remove-purposely"]["==External links=="] += 1
            with open("edit_history/iter/_remove_purposely.json", "a") as f:
                f.write(f"{json.dumps(link_obj)}\n")
    except Exception as e:
        pass

print(json.dumps(STATS, indent=4))