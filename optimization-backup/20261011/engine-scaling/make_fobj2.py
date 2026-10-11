# Floor-object index candidate: engines/fobj2 = invwt + incremental nh_fobj window (prepend/remove in place, no chain walk).
import shutil,subprocess
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
dst=CS/'fobj2/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/'invwt/source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('tools/globals.def',"global | cold | int | nh_fobj_count | | 0\n","global | cold | int | nh_fobj_count | | 0\nglobal | cold | int | nh_fobj_lo | | 0\n")
rep('include/hack.h',"extern void NDECL(nh_fobj_invalidate);\n","extern void NDECL(nh_fobj_invalidate);\nextern void FDECL(nh_fobj_placed, (struct obj *));\nextern void FDECL(nh_fobj_removed, (struct obj *));\n")
rep('src/monmove.c',"""static void
nh_fobj_build(void)
{
    struct obj *o;
    int n = 0;
    for (o = fobj; o; o = o->nobj) {
        if (n == 2048) { nh_fobj_count = -1; nh_fobj_valid = 1; return; }
        nh_fobj_ptr[n] = o;
        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        n++;
    }
    nh_fobj_count = n; nh_fobj_valid = 1;
}
""","""/* The index lives in the window [nh_fobj_lo, nh_fobj_lo + nh_fobj_count) parked
 * at the top of the arrays, so place_object (a chain prepend) is one store and
 * remove_object shifts only the newer prefix. Other chain edits still invalidate. */
static void
nh_fobj_build(void)
{
    struct obj *o;
    int n = 0;
    for (o = fobj; o; o = o->nobj) {
        if (n == 2048) { nh_fobj_count = -1; nh_fobj_valid = 1; return; }
        nh_fobj_ptr[n] = o;
        nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
        n++;
    }
    if (n && n < 2048) {
        memmove(nh_fobj_ptr + 2048 - n, nh_fobj_ptr, n * sizeof nh_fobj_ptr[0]);
        memmove(nh_fobj_x + 2048 - n, nh_fobj_x, n * sizeof nh_fobj_x[0]);
        memmove(nh_fobj_y + 2048 - n, nh_fobj_y, n * sizeof nh_fobj_y[0]);
    }
    nh_fobj_lo = 2048 - n; nh_fobj_count = n; nh_fobj_valid = 1;
}

void
nh_fobj_placed(struct obj *o)
{
    nh_fobj_generation++;
    if (!nh_fobj_valid || nh_fobj_count < 0) return;
    if (nh_fobj_lo == 0) { nh_fobj_valid = 0; return; }
    nh_fobj_lo--;
    nh_fobj_ptr[nh_fobj_lo] = o;
    nh_fobj_x[nh_fobj_lo] = o->ox; nh_fobj_y[nh_fobj_lo] = o->oy;
    nh_fobj_count++;
}

void
nh_fobj_removed(struct obj *o)
{
    int i, lo = nh_fobj_lo, hi;
    nh_fobj_generation++;
    if (!nh_fobj_valid || nh_fobj_count < 0) return;
    hi = lo + nh_fobj_count;
    for (i = lo; i < hi; i++)
        if (nh_fobj_ptr[i] == o) break;
    if (i == hi) { nh_fobj_valid = 0; return; }
    memmove(nh_fobj_ptr + lo + 1, nh_fobj_ptr + lo, (i - lo) * sizeof nh_fobj_ptr[0]);
    memmove(nh_fobj_x + lo + 1, nh_fobj_x + lo, (i - lo) * sizeof nh_fobj_x[0]);
    memmove(nh_fobj_y + lo + 1, nh_fobj_y + lo, (i - lo) * sizeof nh_fobj_y[0]);
    nh_fobj_lo++; nh_fobj_count--;
}
""")
rep('src/monmove.c',"        cursor->generation = nh_fobj_generation;\n        cursor->index = 0;\n","        cursor->generation = nh_fobj_generation;\n        cursor->index = nh_fobj_lo;\n")
rep('src/monmove.c',"        while (cursor->index + 8 <= nh_fobj_count) {","        while (cursor->index + 8 <= nh_fobj_lo + nh_fobj_count) {")
rep('src/monmove.c',"    while (cursor->index < nh_fobj_count) {","    while (cursor->index < nh_fobj_lo + nh_fobj_count) {")
rep('src/monmove.c',"""#ifdef NLE_FOBJ_VERIFY
    {
        int n = 0;
        for (o = fobj; o; o = o->nobj, n++)
            if (n >= nh_fobj_count || nh_fobj_ptr[n] != o
                || nh_fobj_x[n] != o->ox || nh_fobj_y[n] != o->oy)
                panic("floor index mismatch at %d", n);
        if (n != nh_fobj_count) panic("floor index count mismatch");
    }
#endif""","""#ifdef NLE_FOBJ_VERIFY
    if (!prev && nh_fobj_count >= 0) {
        int n = 0, bad = 0;
        for (o = fobj; o; o = o->nobj, n++)
            if (n >= nh_fobj_count || nh_fobj_ptr[nh_fobj_lo + n] != o
                || nh_fobj_x[nh_fobj_lo + n] != o->ox || nh_fobj_y[nh_fobj_lo + n] != o->oy) { bad = 1; break; }
        if (bad || n != nh_fobj_count) {
            fprintf(stderr, "FOBJ_MISMATCH turn=%ld n=%d count=%d lo=%d\\n", moves, n, nh_fobj_count, nh_fobj_lo);
            nh_fobj_build();
            cursor->generation = nh_fobj_generation;
            cursor->index = nh_fobj_lo;
            cursor->fallback = nh_fobj_count < 0;
        }
    }
#endif""")
rep('src/mkobj.c',"    otmp->nobj = fobj;\n    fobj = otmp;\n    nh_fobj_invalidate();\n    nh_pile_update(x, y);","    otmp->nobj = fobj;\n    fobj = otmp;\n    nh_fobj_placed(otmp);\n    nh_pile_update(x, y);")
rep('src/mkobj.c',"    nh_pile_update(x, y);\n    nh_fobj_invalidate();\n    extract_nobj(otmp, &fobj);","    nh_pile_update(x, y);\n    nh_fobj_removed(otmp);\n    extract_nobj(otmp, &fobj);")
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); print(out.stdout.strip(), out.stderr.strip()[:300])
d=subprocess.run(['diff','-u',str(CS/'invwt/source/include/nh_ctx_gen.h'),str(dst/'include/nh_ctx_gen.h')],capture_output=True,text=True).stdout
print('ctx header diff lines:', [l for l in d.splitlines() if l.startswith(('+','-')) and not l.startswith(('+++','---'))])
print('fobj2 source ready')
