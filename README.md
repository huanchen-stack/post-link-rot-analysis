# post-link-rot-analysis

1. `parse.py`: read and parse ext dump; output is the first revision in 2019/2014 as well as revision meta
2. `extract_links.py`: read the first revisions and extract external links using `mwparserfromhell`
3. `analysis_augment.py`: analysis the extracted external links, group them into [live-only, augmented, archive-only]
4. `merge_by_host.py`: prep probe for live-only links, group links by hostnames so that politeness is not performance bottleneck
5. `probe_queue_make.py`: randomize probe sequence to improve politeness
6. `probe_live.py`: GET requests to live links
7. `group_broken_links.py`: group broken links by DIR/article name; this is to help batched analysis
8. `iter_edit_history.py`: re-iterate through all edit histories, find date of 1st [augmentation, removal]
9. `probe_hisory.py`
