#! /bin/bash

# print folder contents for debugging
printf "\n\nContents:\n\n"
ls

# fetch latest citations from member ORCIDs
python3 _scripts/fetch_orcid.py

# run cite process
python3 _cite/cite.py

# run jekyll serve in hot-reload mode
# rerun whenever _config.yaml changes (jekyll hot-reload doesn't work with this file)
watchmedo auto-restart \
    --debug-force-polling \
    --patterns="_config.yaml" \
    --signal SIGTERM \
    -- bundle exec jekyll serve --open-url --force_polling --livereload --trace --host=0.0.0.0 \
    | sed "s/LiveReload address.*//g;s/0.0.0.0/localhost/g" &

# rerun cite process whenever _data files change
watchmedo shell-command \
    --debug-force-polling \
    --recursive \
    --wait \
    --command="python3 _scripts/fetch_orcid.py && python3 _cite/cite.py" \
    --patterns="_data/sources*;_data/orcid*;_data/pubmed*;_data/google-scholar*;_members/*.md;_scripts/fetch_orcid.py" \
