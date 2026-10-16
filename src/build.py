# Shared build script: identical in alevel-biology, alevel-chemistry and alevel-maths.
# Subject-specific text lives in content/site.yaml. Diagrams live in diagrams/<name>.svg
# and are attached to a summary section with `fig: <name>` and `cap: "<caption>"`.
import yaml, json, glob, sys, collections, re, os, html

TEMPLATE_VERSION = 3

SITE = yaml.safe_load(open("content/site.yaml"))
PLAN = SITE["plan"]

def load_svg(name, cap):
    path = f"diagrams/{name}.svg"
    if not os.path.exists(path): return None, f"missing {path}"
    svg = open(path).read()
    svg = re.sub(r"<\?xml[^>]*\?>", "", svg).strip()
    # drop metadata some file-transfer tools inject (e.g. C2PA provenance)
    svg = re.sub(r"<metadata>.*?</metadata>", "", svg, flags=re.S)
    svg = re.sub(r'\s+xmlns:(?!xlink)\w+="[^"]*"', "", svg)
    for bad in ("<script", "<style", "<foreignObject", "<image"):
        if bad in svg: return None, f"{path} contains {bad}"
    if not svg.startswith("<svg") or "viewBox" not in svg: return None, f"{path} needs an <svg> root with a viewBox"
    if not cap: return None, f"{name}: figure needs a cap (caption)"
    # Prefix ids so two figures on one page can't clash
    pre = "f-" + re.sub(r"[^a-z0-9]", "", name.lower()) + "-"
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}{m.group(1)})', svg)
    svg = re.sub(r'href="#([^"]+)"', lambda m: f'href="#{pre}{m.group(1)}"', svg)
    label = html.escape(re.sub(r"\*\*|`", "", cap), quote=True)
    svg = svg.replace("<svg", f'<svg role="img" aria-label="{label}"', 1)
    return svg, None

errors = []
units = []
figs_used = set()
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
    for s in u.get("summary", []):
        if "fig" in s:
            svg, err = load_svg(s["fig"], s.get("cap", ""))
            if err: errors.append(f"{u['id']}: {err}")
            else:
                s["svg"] = svg; figs_used.add(s["fig"])

units.sort(key=lambda u: u["order"])
unused = sorted(set(os.path.splitext(os.path.basename(f))[0] for f in glob.glob("diagrams/*.svg")) - figs_used)
if unused: print("Note: diagrams not used by any topic:", ", ".join(unused))
pr = yaml.safe_load(open("content/practicals.yaml"))
ids = {u["id"] for u in units}
vid_count = 0
for p in pr:
    if p["unit"] not in ids:
        p["_pending"] = True
    for v in p.get("videos", []) or []:
        if not re.fullmatch(r"[A-Za-z0-9_-]{11}", str(v.get("yt", ""))):
            errors.append(f"RP{p['n']}: video needs an 11-character YouTube id in yt")
        if not v.get("title") or not v.get("by"):
            errors.append(f"RP{p['n']}: video needs title and by")
        vid_count += 1

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
print(f"OK (template v{TEMPLATE_VERSION}): {len(units)} units, {sum(len(u['questions']) for u in units)} questions, {len(pr)} practicals, {vid_count} videos, {len(figs_used)} diagrams")
for u in units:
    print(f"  {u['id']:5} {dict(sorted(collections.Counter(q['a'] for q in u['questions']).items()))}")
