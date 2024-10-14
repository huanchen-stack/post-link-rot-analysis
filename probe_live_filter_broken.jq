#!bin/bash

I_FILE="probe/probe_live/probe_live_results_patched.json"
O_FILE="probe/probe_live/probe_live_results_broken.json"
jq -s '[.[] | select(.is_broken == true)]' < "$I_FILE" > "$O_FILE"
