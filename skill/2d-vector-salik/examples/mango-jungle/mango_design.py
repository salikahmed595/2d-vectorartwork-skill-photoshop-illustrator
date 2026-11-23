"""Mango - Jungle Sunrise Gamer. Writes drawing.json for ai_draw.py: one layer per character part, scene on its own layers.
No AI generation; every path is hand-placed vector data in mango_char.py / mango_bg.py."""
import json
from pathlib import Path

import mango_bg as bg
import mango_char as ch

HERE = Path(__file__).parent
DOC = "mango-pfp.ai"


def build():
    L = []

    def add(layer, items, clear=True, **kw):
        e = {"layer": layer, "clear": clear, "items": items}
        e.update(kw)
        L.append(e)

    add("Background/Sky", bg.sky_items())
    add("Background/Sun", bg.sun_items())
    add("Background/Clouds", bg.cloud_items())
    add("Background/Far jungle", bg.far_jungle_items())
    add("Background/Mist", bg.mist_items())
    add("Background/Mid jungle", bg.mid_jungle_items())
    add("Background/Tall trees", bg.tall_tree_items())
    add("Background/Vines back", bg.vines_back_items())
    add("Background/Canopy", bg.canopy_items())
    add("Scene/Ground", bg.ground_items())
    add("Scene/Ground plants", bg.ground_detail_items())
    add("Mango/Cape", ch.cape_items())
    add("Mango/Log", bg.log_items())                 # prop inside the character group: in front of the cape, under the feet
    add("Mango/Contact shadows", bg.contact_items())
    add("Mango/Feet", ch.feet_items())
    add("Mango/Body", ch.body_items(), clip=ch.body_clip(), outline={"stroke": ch.LINE, "width": 7})
    add("Mango/Leaves", ch.leaf_group_items())
    add("Mango/Mouth & blush", ch.mouth_items())
    cl, il, ll = ch.eye_items("L")
    cr, ir, lr = ch.eye_items("R")
    add("Mango/Eyes", il, clip=cl)
    add("Mango/Eyes", ir, clear=False, clip=cr)
    add("Mango/Eyes", ll + lr, clear=False)
    add("Mango/Brows", ch.brow_items())
    add("Mango/Arms", ch.arm_items())
    add("Mango/Controller", ch.controller_items())
    add("Mango/Hands", ch.hand_items())
    add("Mango/Cape collar", ch.collar_items())
    add("Foreground/Vines front", bg.vines_front_items())
    add("Foreground/Leaves", bg.foreground_items())
    add("FX/Particles", bg.particle_items())
    spec = {"doc": DOC, "layers": L}
    out = HERE / "drawing.json"
    out.write_text(json.dumps(spec), encoding="utf-8")
    n = sum(len(e["items"]) for e in L)
    print(f"wrote {out.name}: {len(L)} entries, {n} items, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    build()
