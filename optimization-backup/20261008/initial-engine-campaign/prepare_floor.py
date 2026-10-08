from pathlib import Path
import subprocess
r=Path(__file__).resolve().parent;s=r/'engine-floor'
def replace(file,old,new):
 p=s/file;t=p.read_text();assert t.count(old)==1,(file,t.count(old));p.write_text(t.replace(old,new))
p=s/'tools/globals.def'
with p.open('a') as f:f.write('''
# Ordered floor-object search cache. Cold section avoids shifting hot state.
global | cold | unsigned long | nh_fobj_generation | | 0
global | cold | int | nh_fobj_valid | | 0
global | cold | int | nh_fobj_count | | 0
global | cold | short | nh_fobj_x | [2048] | 0
global | cold | short | nh_fobj_y | [2048] | 0
global | cold | struct obj * | nh_fobj_ptr | [2048] | 0
''')
subprocess.run(['python3','tools/gen_ctx.py'],cwd=s,check=True)
replace(Path('include/hack.h'),'extern void NDECL(nh_typ_sync);','''extern void NDECL(nh_typ_sync);
struct nh_fobj_cursor { unsigned long generation; int index, fallback; };
extern void NDECL(nh_fobj_invalidate);
extern struct obj *FDECL(nh_fobj_next, (struct nh_fobj_cursor *, struct obj *, int, int, int, int));''')
code='''
/* Preserve fobj order. A mutation during iteration switches that iterator to
 * the original linked-list walk from prev->nobj; never rebuild under a cursor. */
void
nh_fobj_invalidate(void)
{
    nh_fobj_valid = 0;
    nh_fobj_generation++;
}

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
    nh_fobj_count = n; nh_fobj_valid = 1;
}

struct obj *
nh_fobj_next(struct nh_fobj_cursor *cursor, struct obj *prev,
             int lx, int hx, int ly, int hy)
{
    struct obj *o;
    if (!prev) {
        if (!nh_fobj_valid) nh_fobj_build();
        cursor->generation = nh_fobj_generation;
        cursor->index = 0;
        cursor->fallback = nh_fobj_count < 0;
    } else if (cursor->generation != nh_fobj_generation) {
        cursor->fallback = 1;
    }
    if (cursor->fallback) {
        for (o = prev ? prev->nobj : fobj; o; o = o->nobj)
            if (o->ox >= lx && o->ox <= hx && o->oy >= ly && o->oy <= hy)
                return o;
        return (struct obj *) 0;
    }
#ifdef NLE_FOBJ_VERIFY
    {
        int n = 0;
        for (o = fobj; o; o = o->nobj, n++)
            if (n >= nh_fobj_count || nh_fobj_ptr[n] != o
                || nh_fobj_x[n] != o->ox || nh_fobj_y[n] != o->oy)
                panic("floor index mismatch at %d", n);
        if (n != nh_fobj_count) panic("floor index count mismatch");
    }
#endif
    while (cursor->index < nh_fobj_count) {
        int i = cursor->index++;
        if (nh_fobj_x[i] >= lx && nh_fobj_x[i] <= hx
            && nh_fobj_y[i] >= ly && nh_fobj_y[i] <= hy)
            return nh_fobj_ptr[i];
    }
    return (struct obj *) 0;
}

'''
replace(Path('src/monmove.c'),'int\nm_move(mtmp, after)',code+'int\nm_move(mtmp, after)')
replace(Path('src/monmove.c'),'        int oomx, oomy, lmx, lmy;','        int oomx, oomy, lmx, lmy;\n        struct nh_fobj_cursor cursor;')
replace(Path('src/monmove.c'),'            for (otmp = fobj; otmp; otmp = otmp->nobj) {','''            for (otmp = nh_fobj_next(&cursor, (struct obj *) 0, lmx, oomx, lmy, oomy);
                 otmp;
                 otmp = nh_fobj_next(&cursor, otmp, lmx, oomx, lmy, oomy)) {''')
replace(Path('src/mkobj.c'),'    if (obj->where == OBJ_FLOOR)\n        obj->nexthere = otmp;','''    if (obj->where == OBJ_FLOOR) {
        obj->nexthere = otmp;
        nh_fobj_invalidate();
    }''')
replace(Path('src/mkobj.c'),'        extract_nobj(obj, &fobj);','        nh_fobj_invalidate();\n        extract_nobj(obj, &fobj);')
replace(Path('src/mkobj.c'),'    fobj = otmp;','    fobj = otmp;\n    nh_fobj_invalidate();')
replace(Path('src/mkobj.c'),'    extract_nobj(otmp, &fobj);','    nh_fobj_invalidate();\n    extract_nobj(otmp, &fobj);')
replace(Path('src/mon.c'),'    register boolean somebody_can_move = FALSE;','    register boolean somebody_can_move = FALSE;\n\n    nh_fobj_invalidate();')
replace(Path('src/nle.c'),'    nle->observation = obs;\n    /* tty gating','    nh_fobj_invalidate();\n    nle->observation = obs;\n    /* tty gating')
replace(Path('src/restore.c'),'    while ((otmp = fobj) != 0) {','    nh_fobj_invalidate();\n    while ((otmp = fobj) != 0) {')
replace(Path('src/restore.c'),'    fobj = restobjchn(fd, ghostly, FALSE);','    nh_fobj_invalidate();\n    fobj = restobjchn(fd, ghostly, FALSE);')
replace(Path('src/save.c'),'        fobj = level.buriedobjlist = billobjs = 0;','        nh_fobj_invalidate();\n        fobj = level.buriedobjlist = billobjs = 0;')
replace(Path('src/save.c'),'    fobj = (struct obj *) 0;','    nh_fobj_invalidate();\n    fobj = (struct obj *) 0;')
print('Prepared ordered floor cache candidate on03; not built or accepted')
