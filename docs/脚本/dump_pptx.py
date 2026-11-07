import sys
from pptx import Presentation
from pptx.util import Emu

path = sys.argv[1]
prs = Presentation(path)
print("slides:", len(prs.slides), "size:", prs.slide_width, prs.slide_height)
for i, slide in enumerate(prs.slides, 1):
    print("=" * 60)
    print(f"[Slide {i}] layout={slide.slide_layout.name}")
    def walk(shapes, indent=0):
        for sh in shapes:
            pre = "  " * indent
            t = sh.shape_type
            if sh.has_text_frame:
                txt = "\n".join(p.text for p in sh.text_frame.paragraphs)
                if txt.strip():
                    print(f"{pre}- {sh.name} ({t})")
                    for line in txt.split("\n"):
                        print(f"{pre}    | {line}")
            elif sh.has_table:
                print(f"{pre}- TABLE {sh.name}")
                for r in sh.table.rows:
                    print(f"{pre}    | " + " || ".join(c.text.replace("\n", " / ") for c in r.cells))
            elif sh.has_chart:
                print(f"{pre}- CHART {sh.name}")
            elif t == 6:  # group
                print(f"{pre}- GROUP {sh.name}")
                walk(sh.shapes, indent + 1)
            else:
                print(f"{pre}- {sh.name} ({t})")
    walk(slide.shapes)
    if slide.has_notes_slide:
        nt = slide.notes_slide.notes_text_frame.text
        if nt.strip():
            print("[notes]", nt)
