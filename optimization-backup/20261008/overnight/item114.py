from pathlib import Path
import subprocess,difflib
r=Path(__file__).parent;p=r/'engine-source/src/muse.c';before=p.read_text();assert before==(r/'pgo61-source/src/muse.c').read_text()
a='''    int typ = obj->otyp;

    if (is_animal(mon->data) || mindless(mon->data)'''
b='''    int typ = obj->otyp;

    /* Classes with no useful items need no monster-property reads.
       Keep the original type-only exceptions even for unusual objects. */
    if (typ != WAN_MAKE_INVISIBLE && typ != POT_INVISIBILITY
        && typ != WAN_SPEED_MONSTER && typ != POT_SPEED) {
        switch (obj->oclass) {
        case WAND_CLASS: case POTION_CLASS: case SCROLL_CLASS:
        case AMULET_CLASS: case TOOL_CLASS: case FOOD_CLASS:
            break;
        default:
            return FALSE;
        }
    }

    if (is_animal(mon->data) || mindless(mon->data)'''
assert before.count(a)==1;after=before.replace(a,b)
(r/'item114.patch').write_text(''.join(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/src/muse.c',tofile='b/src/muse.c')))
p.write_text(after)
try:subprocess.run(['python',str(r/'engine_screen_alloc62.py'),'item114'],check=True)
finally:p.write_text(before)
