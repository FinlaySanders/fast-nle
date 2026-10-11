# dv5 = <base> + lazy screen flush: flush_screen() only marks the screen dirty; the print to the window port (and the deferred bot())
# happens once, when the window port is about to fill an observation. Same final screen store, fewer print_glyph calls.
import shutil,subprocess,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'dv4'
dst=CS/'dv5/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | int | nh_invwt_valid | | 0\n","global | hot | int | nh_invwt_valid | | 0\nglobal | hot | int | nh_flush_pending | | 0\nglobal | hot | int | nh_flush_cursor | | 0\n")
rep('include/extern.h',"E void FDECL(flush_screen, (int));\n","E void FDECL(flush_screen, (int));\nE void FDECL(nh_flush_now, (int));\nE void NDECL(nh_flush_deferred);\n")
rep('src/display.c',"""    /* Flushing/delay_flushing promoted to ctx fields */
    register int x, y;

    if (cursor_on_u == -1)
        delay_flushing = !delay_flushing;
    if (delay_flushing)
        return;
    if (flushing)
        return; /* if already flushing then return */
    flushing = 1;
""","""    /* Flushing/delay_flushing promoted to ctx fields */
    if (cursor_on_u == -1)
        delay_flushing = !delay_flushing;
    if (delay_flushing)
        return;
    if (flushing)
        return; /* if already flushing then return */
    /* Defer the print to the next observation: the window port only ever reads the final screen. */
    nh_flush_pending = 1;
    if (cursor_on_u > 0)
        nh_flush_cursor = 1;
}

/* The window port calls this before it reads the screen for an observation. */
void
nh_flush_deferred()
{
    int c;

    if (!nh_flush_pending)
        return;
    c = nh_flush_cursor;
    nh_flush_pending = 0;
    nh_flush_cursor = 0;
    nh_flush_now(c);
}

void
nh_flush_now(cursor_on_u)
int cursor_on_u;
{
    register int x, y;

    if (flushing)
        return;
    flushing = 1;
""")
rep('win/rl/winrl.cc',"NetHackRL::fill_obs(nle_obs *obs)\n{\n","NetHackRL::fill_obs(nle_obs *obs)\n{\n    nh_flush_deferred();\n")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
print('dv5 source written from',BASE)
