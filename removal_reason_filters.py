import json
import os
import re


FILTERS = [
    # our interest
    # r"fix link",
    # r"fix ref",
    # r"dead link",
    # r"found working.*links",
    # r"ref.* fix",
    # r"remove link",
    # r"remove ref",

    # ---???---
    r"external links",
    r"archive.today",
    r"archive.is",
    r"overlinking",
    r"too many link",
    r"too many ref",

    # script assisted formats
    r"script.*assisted fix.*\[\[mos:\s*.*?\]\]",
    r"\[\[.*use this bot\]\]",
    r"citation bot",
    r"referenceexpander",
    r"waybackmedic",

    # Content based
    r"observance",
    r"source.*skeptical",
    r"factual",
    r"vague.*not.*related",
    r"repetition",
    r"remove.*region-specific",
    r"rule change",
    r"remove.*conjecture from",
    r"not relevant",
    r"wrong",
    r"standardize.*citation",
    r"update",
    r"reorganise",

    # section moves
    r"moving.*to.*",
    r"move.*to.*",
    r"section.*move",

    # empty
    # r"^\s*/\*.*\*/\s*$",
    # r"^$",

    # # misc
    # r"detail revision",
    # r"cleaning up of section",
    # r"filled in 2 bare reference",
    # r"neither of the sources",
    # r"myth",
    # r"tidy some references"
]

# print(len(results))
# # Apply regex-based filtering
# # len(r["remove-purposely"][-1]["edit_meta_from"].get("comment", "")) <= 200 and 

# results = [
#     r for r in results
#     if not any(
#         re.search(
#             f, 
#             r["remove-purposely"][-1]["edit_meta_from"].get("comment", "").lower()
#         ) for f in filters
#     )
# ]

# print(len(results))

# probe_archive_queue = []

# for item in results:
# # item = results[0]
#     oldid = item["remove-purposely"][-1]["edit_meta_from"]["id"]
#     article_name = item["article_name"]
#     wiki_diff_link = f"https://en.wikipedia.org/w/index.php?title={article_name.replace(" ", "_")}&diff=prev&oldid={oldid}"

# # print(json.dumps(results[0], indent=2))
# # print(json.dumps({
#     probe_archive_queue.append({
#         "url": item["url"],
#         "wiki_diff_link": wiki_diff_link,
#         "timestamp": item["remove-purposely"][-1]["edit_meta_from"]["timestamp"],
#         "comment": item["remove-purposely"][-1]["edit_meta_from"].get("comment", ""),
#         "username": item["remove-purposely"][-1]["edit_meta_from"].get("username", item["remove-purposely"][-1]["edit_meta_from"].get("ip", "Unknown")),
#     })

# print(probe_archive_queue[0])
