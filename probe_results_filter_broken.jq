jq -s '[.[] | select(.is_broken == true)]' < probe_results.json > probe_results_broken.json
