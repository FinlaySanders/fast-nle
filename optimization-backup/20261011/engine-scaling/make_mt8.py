# mt8 = <base> + S3 done right: movement-class planes cached per game across turns (keyed by the class bits, invalidated by a (bars, door, pool, lava, drawbridge, altar, tree, garlic, boulder,
# scare, trap, gas) terrain/gas generation) give the neighbour query its candidate set in 3 loads; per-cell facts come from the column words maintained
# at the existing update sites. Cell order, info flags and the mux/muy side effect are unchanged. Twin: -DNH_MOVEMENT_MASK_VERIFY.
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt7'
dst=CS/'mt8/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
# 1. column struct + generic bit setter
rep('include/movement_masks.h',"struct nh_move_column { unsigned int nonrock, occupied; };",
"""struct nh_move_column { unsigned int nonrock, occupied, bars, door, pool, lava, dbridge, altar, tree, garlic, boulder, scare, trap, gas; };
static inline void
nh_move_set_bit(unsigned int *w, int y, int on)
{
    unsigned int bit = 1U << y;
    if (on) *w |= bit;
    else *w &= ~bit;
}""")
# 2. terrain-derived classes at every type write
rep('include/hack.h',"""    nh_typ_plane[x][y] = typ;
    nh_move_set_terrain(level.move_columns, x, y, !IS_ROCK(typ));
}""","""    struct nh_move_column *c = &level.move_columns[x + 1];
    nh_typ_plane[x][y] = typ;
    nh_move_set_terrain(level.move_columns, x, y, !IS_ROCK(typ));
    nh_move_set_bit(&c->bars, y, typ == IRONBARS);
    nh_move_set_bit(&c->door, y, typ == DOOR);
    nh_move_set_bit(&c->pool, y, typ == POOL || typ == MOAT || typ == WATER);
    nh_move_set_bit(&c->lava, y, typ == LAVAPOOL);
    nh_move_set_bit(&c->dbridge, y, typ == DRAWBRIDGE_UP);
    nh_move_set_bit(&c->altar, y, typ == ALTAR);
    nh_move_set_bit(&c->tree, y, typ == TREE);
    nh_plane_gen++;
}""")
# 3. pile / trap / gas classes
rep('src/mon.c',"""    NH_SUMMARY(x, y).move_pile = f >> 13;
    NH_SUMMARY(x, y).move_obj_present = OBJ_AT(x, y);
}""","""    NH_SUMMARY(x, y).move_pile = f >> 13;
    NH_SUMMARY(x, y).move_obj_present = OBJ_AT(x, y);
    nh_move_set_bit(&level.move_columns[x + 1].garlic, y, (f & MV_GARLIC) != 0);
    nh_move_set_bit(&level.move_columns[x + 1].boulder, y, (f & MV_BOULDER) != 0);
    nh_move_set_bit(&level.move_columns[x + 1].scare, y, (f & MV_SCARE) != 0);
}""")
rep('src/mon.c',"""    NH_SUMMARY(x, y).move_trap = t ? t->ttyp : 0;
    NH_SUMMARY(x, y).move_trap_present = t != 0;
}""","""    NH_SUMMARY(x, y).move_trap = t ? t->ttyp : 0;
    NH_SUMMARY(x, y).move_trap_present = t != 0;
    nh_move_set_bit(&level.move_columns[x + 1].trap, y, t != 0);
}""")
rep('src/region.c',"        NH_SUMMARY(x, y).move_gas = reg && reg->glyph == cmap_to_glyph(S_poisoncloud);",
"""        NH_SUMMARY(x, y).move_gas = reg && reg->glyph == cmap_to_glyph(S_poisoncloud);
        nh_move_set_bit(&level.move_columns[x + 1].gas, y, NH_SUMMARY(x, y).move_gas);
        nh_plane_gen++;""")
rep('src/mon.c',"""        if (domains & NH_MOVE_GAS) NH_SUMMARY(x, y).move_gas = 0;
    }""","""        if (domains & NH_MOVE_GAS) NH_SUMMARY(x, y).move_gas = 0;
    }
    for (x = 0; x < COLNO + 2; x++) {
        if (domains & NH_MOVE_PILES)
            level.move_columns[x].garlic = level.move_columns[x].boulder = level.move_columns[x].scare = 0;
        if (domains & NH_MOVE_TRAPS) level.move_columns[x].trap = 0;
        if (domains & NH_MOVE_GAS) level.move_columns[x].gas = 0;
    }
    nh_plane_gen++;""")
rep('src/mklev.c',"""    for (x = 0; x < COLNO; x++) {
        for (y = 0; y < ROWNO; y++) {
            nh_copy_terrain(&NH_TILE(x, y), &zerorm);""","""    nh_tile_clear_entities(NH_MOVE_PILES | NH_MOVE_TRAPS | NH_MOVE_GAS);
    for (x = 0; x < COLNO; x++) {
        for (y = 0; y < ROWNO; y++) {
            nh_copy_terrain(&NH_TILE(x, y), &zerorm);""")
import subprocess
# 4. ctx: plane generation + plane cache (8 classes x (COLNO+2) column words)
rep('tools/globals.def',"global | cold | int | nh_fobj_lo | | 0\n","global | cold | int | nh_fobj_lo | | 0\nglobal | hot | unsigned long | nh_plane_gen | | 0\nglobal | cold | struct nh_move_plane | nh_planes | [8] | 0\nglobal | cold | int | nh_plane_next | | 0\n")
rep('include/movement_masks.h',"struct nh_move_column {","struct nh_move_plane { unsigned int key; unsigned long gen; unsigned int col[81]; }; /* COLNO + 2 columns */\nstruct nh_move_column {")
# 5. the query
p=dst/'src/mon.c'; s=p.read_text()
a=s.index('static int mfndpos_masked(mon, poss, info, flag)'); b=s.index('\nint\nmfndpos(struct monst *mon', a)
fn=s[a:b]
i_disp=fn.index('                int dispx, dispy;'); i_pile=fn.index('                if (NH_SUMMARY(nx, ny).move_pile & 2U) {')
inner_hero=fn[i_disp:i_pile].replace('                    if (MON_AT(nx, ny)) {','                    if (occ & cb) {')
i_trap=fn.index('                if (NH_SUMMARY(nx, ny).move_trap_present != 0) {'); i_poss=fn.index('                poss[cnt].x = nx;')
inner_trap=fn[i_trap:i_poss].replace('                if (NH_SUMMARY(nx, ny).move_trap_present != 0) {','                if (CW(nx).trap & rb) {',1)
assert 'MON_AT' not in inner_hero and inner_hero.count('occ & cb')==1
fn=fn.replace("    unsigned int candidates, occupied;\n","    unsigned int candidates, occ, cb, rb, pkey;\n    const unsigned int *pc;\n    boolean rockcells, barsok, gasrej, juiblex, origin_door, origin_door_diag, ispool, islava;\n",1)
i_next=fn.index('nexttry: /* eels prefer the water')
plane_fn = '''
/* Movement-class plane: per column, the rows a monster of this class may enter before the per-cell checks.
 * key bits: 1 rock cells stay (wall/dig), 2 bars allowed, 4 gas rejected, 8 wantpool, 16 poolok, 32 lavaok.
 * Cached per game across turns; invalidated by nh_plane_gen (terrain type writes, gas updates, level load). */
static const unsigned int *
nh_move_plane(unsigned int key)
{
    struct nh_move_plane *pl;
    int i, x;
    for (i = 0; i < 8; i++) {
        pl = &nh_planes[i];
        if (pl->gen && pl->gen == nh_plane_gen && pl->key == key) return pl->col;
    }
    pl = &nh_planes[nh_plane_next]; nh_plane_next = (nh_plane_next + 1) & 7;
    if (!nh_plane_gen) nh_plane_gen = 1; /* generation 0 marks an empty slot */
    pl->key = key; pl->gen = nh_plane_gen;
    for (x = 0; x < COLNO + 2; x++) {
        const struct nh_move_column *c = &level.move_columns[x];
        /* move_columns[i] is map column i-1; nh_move_valid admits map columns 1..COLNO-1 = indices 2..COLNO */
        unsigned int e = (x >= 2 && x <= COLNO) ? ((1U << ROWNO) - 1U) : 0U;
        if (!(key & 1U)) e &= c->nonrock;
        if (!(key & 2U)) e &= ~c->bars;
        if (key & 4U) e &= ~c->gas;
        if (!(key & 16U)) e &= (key & 8U) ? (c->pool | c->dbridge) : ~c->pool;
        if (!(key & 32U)) e &= ~c->lava;
        pl->col[x] = e;
    }
    return pl->col;
}

'''
tail='''nexttry: /* eels prefer the water, but if there is no water nearby,
            they will crawl over land */
    if (mon->mconf) {
        flag |= ALLOW_ALL;
        flag &= ~NOTONL;
    }
    if (!mon->mcansee)
        flag |= ALLOW_SSM;
    cols = &level.move_columns[x];
#define CW(cx) (level.move_columns[(cx) + 1])
    rockcells = (flag & ALLOW_WALL) || rockok || treeok;
    barsok = (flag & ALLOW_BARS) != 0;
    gasrej = !poisongas_ok && !in_poisongas;
    pkey = (rockcells ? 1U : 0U) | (barsok ? 2U : 0U) | (gasrej ? 4U : 0U) | (wantpool ? 8U : 0U) | (poolok ? 16U : 0U) | (lavaok ? 32U : 0U);
    pc = nh_move_plane(pkey) + x; /* pc[0] = column x-1 (col index x), pc[1] = x, pc[2] = x+1 */
    candidates = nh_move_neighbours(pc[0], pc[1], pc[2], y);
    occ = nh_move_neighbours(cols[0].occupied, cols[1].occupied, cols[2].occupied, y);
    if (!(flag & (ALLOW_M | ALLOW_MDISP))
        && !SPWQ(mdat, SPW_DISPLACES, (mdat->mflags3 & M3_DISPLACES))
        && mdat != &mons[PM_PURPLE_WORM]) {
        /* Both hero positions stay on the original path. The old image may
           become obsolete during this loop, so keep the full checks below. */
        candidates &= ~(occ & ~(nh_move_position_bit(x, y, u.ux, u.uy)
                                | nh_move_position_bit(x, y, mon->mux, mon->muy)));
    }
    juiblex = Is_juiblex_level(&u.uz);
    origin_door = IS_DOOR(origin_typ);
    origin_door_diag = origin_door && (origin->rmflags & ~D_BROKEN);
    while (candidates) {
            bit = __builtin_ctz(candidates);
            candidates &= candidates - 1;
            cb = 1U << bit;
            nx = x - 1 + bit / 3;
            ny = y - 1 + bit % 3;
            rb = 1U << ny;
            cell = (const struct rm *) 0;
            if (rockcells) { /* rock may be a candidate: the original terrain logic */
                cell = nh_move_cell(nx, ny);
                cell_typ = TYP_AT(nx, ny);
                if (IS_ROCK(cell_typ)
                    && !((flag & ALLOW_WALL) && nh_cell_passwall(cell, nx, ny))
                    && !((IS_TREE(cell_typ) ? treeok : rockok) && nh_cell_dig(cell)))
                    continue;
            }
            /* KMH -- Added iron bars (bars cells are in the plane only when ALLOW_BARS) */
            if (CW(nx).bars & rb) {
                if (!cell) cell = nh_move_cell(nx, ny);
                if ((cell->rmflags & W_NONDIGGABLE)
                    && (SPWQ(mdat, SPW_RUSTDMG, dmgtype(mdat, AD_RUST))
                        || SPWQ(mdat, SPW_CORRDMG, dmgtype(mdat, AD_CORR))))
                    continue;
            }
            if (CW(nx).door & rb) {
                if (!cell) cell = nh_move_cell(nx, ny);
                if (!(SPWQ(mdat, SPW_AMORPHOUS, amorphous(mdat)) || nh_mover_fog(&mover))
                    && (((cell->rmflags & D_CLOSED) && !(flag & OPENDOOR))
                        || ((cell->rmflags & D_LOCKED)
                            && !(flag & UNLOCKDOOR)))
                    && !thrudoor)
                    continue;
            }
            /* first diagonal checks (tight squeezes handled below) */
            if (nx != x && ny != y
                && (nodiag
                    || origin_door_diag
                    || ((CW(nx).door & rb) && (cell->rmflags & ~D_BROKEN))
                    || ((origin_door || (CW(nx).door & rb))
                        && mover.rogue)
                    /* mustn't pass between adjacent long worm segments,
                       but can attack that way */
                    || ((occ & nh_move_position_bit(x, y, x, ny)) && (occ & nh_move_position_bit(x, y, nx, y))
                        && worm_cross(x, y, nx, ny)
                        && !(occ & cb) && (nx != u.ux || ny != u.uy))))
                continue;
            if (CW(nx).dbridge & rb) { /* drawbridge: pool/lava depend on what is underneath */
                if (!cell) cell = nh_move_cell(nx, ny);
                ispool = !juiblex && (cell->rmflags & DB_UNDER) == DB_MOAT;
                islava = (cell->rmflags & DB_UNDER) == DB_LAVA;
                if (!((ispool == wantpool || poolok) && (lavaok || !islava)))
                    continue;
            }
            {
''' + inner_hero + '''                if (CW(nx).garlic & rb) {
                    if (flag & NOGARLIC) continue;
                    info[cnt] |= NOGARLIC;
                }
                if (CW(nx).boulder & rb) {
                    if (!(flag & ALLOW_ROCK)) continue;
                    info[cnt] |= ALLOW_ROCK;
                }
                if (monseeu && onlineu(nx, ny)) {
                    if (flag & NOTONL)
                        continue;
                    info[cnt] |= NOTONL;
                }
                /* check for diagonal tight squeeze */
                if (nx != x && ny != y && nh_mover_bad_rock(&mover, x, ny)
                    && nh_mover_bad_rock(&mover, nx, y) && nh_mover_squeeze(&mover))
                    continue;
                /* The monster avoids a particular type of trap if it's
                 * familiar with the trap type.  Pets get ALLOW_TRAPS
                 * and checking is done in dogmove.c.  In either case,
                 * "harmless" traps are neither avoided nor marked in info[].
                 */
''' + inner_trap + '''                poss[cnt].x = nx;
                poss[cnt].y = ny;
                cnt++;
            }
        }
#undef CW
    if (!cnt && wantpool && !nh_cell_pool(origin, x, y)) {
        wantpool = FALSE;
        goto nexttry;
    }
    return cnt;
}

'''
fn=plane_fn+fn[:i_next]+tail
s=s[:a]+fn+s[b:]
p.write_text(s)
rep('src/mon.c','        panic("movement count/state mismatch at %d,%d", x, y);','        fprintf(stderr, "MFNDPOS_MISMATCH count turn=%ld at %d,%d\\n", moves, x, y);')
rep('src/mon.c','            panic("movement ordered candidate mismatch at %d,%d", x, y);','            fprintf(stderr, "MFNDPOS_MISMATCH candidate turn=%ld at %d,%d i=%d\\n", moves, x, y, i);')
out=subprocess.run(['python3','tools/gen_ctx.py'],cwd=dst,capture_output=True,text=True); assert out.returncode==0, out.stderr[:400]
print('mt8 source ready (base', BASE+')')
