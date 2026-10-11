# invview2 = invview + explicit view-dirty generation at the inventory field writes that bypass update_inventory():
# BUC setters (bless/unbless/curse/uncurse) and set_bknown; richer verify message (otyp, old/new) to locate the residue.
import shutil,subprocess
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
dst=CS/'invview2/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/'invview/source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | hot | unsigned long | nh_invgen | | 0\n","global | hot | unsigned long | nh_invgen | | 0\nglobal | hot | unsigned long | nh_invview_gen | | 0\n")
rep('include/hack.h',"#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))","#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))\n#define nh_invview_dirty() ((void) (nh_invview_gen++))")
for fn in ['bless','unbless','curse','uncurse']:
    rep('src/mkobj.c',f"\n{fn}(otmp)\nregister struct obj *otmp;\n{{\n",f"\n{fn}(otmp)\nregister struct obj *otmp;\n{{\n    nh_invview_dirty();\n")
rep('src/mkobj.c',"        obj->bknown = onoff;\n        if (obj->where == OBJ_INVENT && moves > 1L)","        obj->bknown = onoff;\n        nh_invview_dirty();\n        if (obj->where == OBJ_INVENT && moves > 1L)")
w=dst/'win/rl/winrl.cc'; s=w.read_text()
def wrep(old,new,count=1):
    global s; assert s.count(old)==count,(s.count(old),old[:70]); s=s.replace(old,new)
wrep("    unsigned inv_disc_gen_seen_ = 0;\n","    unsigned inv_disc_gen_seen_ = 0;\n    unsigned long inv_view_gen_seen_ = ~0ul;\n")
wrep("        if (inv_disc_gen_seen_ != disc_gen_)\n            refresh_inv_state();","        if (inv_disc_gen_seen_ != disc_gen_ || inv_view_gen_seen_ != nh_invview_gen)\n            refresh_inv_state();",2)
wrep("    inv_disc_gen_seen_ = disc_gen_;\n","    inv_disc_gen_seen_ = disc_gen_;\n    inv_view_gen_seen_ = nh_invview_gen;\n")
wrep('                fprintf(stderr, "INVVIEW_MISMATCH turn=%ld slot=%d field=%d\\n", moves, slot, field);',
'''                {
                    int otyp = -1, k = 0; struct obj *o;
                    for (o = invent; o && k < slot; o = o->nobj, ++k) ;
                    if (o) otyp = o->otyp;
                    int idx = field < 99 ? slot * NLE_INV_STATE_FIELDS + field : -1;
                    fprintf(stderr, "INVVIEW_MISMATCH turn=%ld slot=%d field=%d otyp=%d old=%d new=%d\\n", moves, slot, field, otyp,
                            idx >= 0 ? (int) st_saved[idx] : (int) tg_saved[slot], idx >= 0 ? (int) inv_state_cache_[idx] : (int) inv_true_cache_[slot]);
                }''')
w.write_text(s)
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:300]
print('invview2 source ready')
