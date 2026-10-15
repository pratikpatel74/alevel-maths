import yaml, json, glob, sys, collections, re

SITE = yaml.safe_load(open("content/site.yaml"))
PLAN = SITE["plan"]

errors = []
units = []
for f in sorted(glob.glob("content/u*.yaml")):
    u = yaml.safe_load(open(f))
    units.append(u)
    qs = u["questions"]
    if len(qs) != 22:
        errors.append(f"{u['id']}: {len(qs)} questions")
    pos = collections.Counter()
    seen = set()
    for i, q in enumerate(qs):
        if len(q["o"]) != 4: errors.append(f"{u['id']} q{i}: {len(q['o'])} options")
        if len(set(q["o"])) != 4: errors.append(f"{u['id']} q{i}: duplicate options")
        if q["a"] not in range(4): errors.append(f"{u['id']} q{i}: bad answer index")
        if q["q"] in seen: errors.append(f"{u['id']} q{i}: duplicate question")
        seen.add(q["q"])
        if not q.get("e"): errors.append(f"{u['id']} q{i}: no explanation")
        pos[q["a"]] += 1
    if pos and max(pos.values()) > 9:
        errors.append(f"{u['id']}: answer positions skewed {dict(pos)}")
    for k in ("id", "section", "spec", "title", "desc", "summary"):
        if k not in u: errors.append(f"{u.get('id')}: missing {k}")

units.sort(key=lambda u: u["order"])
pr = yaml.safe_load(open("content/practicals.yaml"))
ids = {u["id"] for u in units}
for p in pr:
    if p["unit"] not in ids:
        p["_pending"] = True

# practicals whose unit isn't built yet still show; link handled in page
if errors:
    print("\n".join(errors)); sys.exit(1)

data = {
    "meta": SITE["meta"],
    "plan": PLAN,
    "sections": {s["code"]: s["name"] for s in PLAN},
    "units": units,
    "practicals": pr,
}
tpl = open("template.html").read().replace("__TITLE__", SITE["meta"]["title"])
js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
open("../index.html", "w").write(tpl.replace("__DATA__", js))
print(f"OK: {len(units)} units, {sum(len(u['questions']) for u in units)} questions, {len(pr)} practicals")
for u in units:
    print(f"  {u['id']:5} {dict(sorted(collections.Counter(q['a'] for q in u['questions']).items()))}")
