"""Builds every profile image from this folder's generators into out/."""
import importlib.util, json, os, re
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
s = load("sheets", "sheets.py")
out = {"gate.svg": load("make_gate", "make_gate.py").build(), "sheet-reggate.svg": s.reggate(), "sheet-spillway.svg": s.spillway(), "sheet-certified-blind.svg": s.certified_blind(), "sheet-openai.svg": s.openai_card(),
       "sheet-undo.svg": s.undo_or_ask(), "sheet-flow-record.svg": s.flow_record(json.load(open("stats-snapshot.json"))), "sheet-fleet.svg": s.fleet()}
for n in range(1, 8):
    out[f"seam-{n}.svg"] = load(f"seam_{n}", f"seams/seam_{n}.py").build(s)
for name, body in out.items():
    assert not re.search(r'[ ;"]nan[ ;"]', body) and "<script" not in body and "foreignObject" not in body, name
    open(os.path.join("..", "assets", name), "w").write(body)
print(len(out), "images,", sum(len(b) for b in out.values()) // 1024, "KB")
