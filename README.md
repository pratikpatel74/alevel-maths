# AQA A-level Maths Study Hub (7357)

Topic summaries with worked examples and 22-question quiz pools for Pure, Statistics and Mechanics, Years 1 and 2.

- `index.html` — the whole site (self-contained, no build needed to host)
- `src/content/*.yaml` — topic content, examples, questions and site settings
- `src/build.py` — rebuilds `index.html` from the content

To rebuild after editing content:

    cd src && pip install pyyaml && python3 build.py
