# mt4 = <base> + S3: the neighbour query reads per-class column masks (bars, door, pool, lava, drawbridge, altar, tree, garlic, boulder,
# scare, trap, gas) maintained at the existing per-cell update sites, so the common floor cell needs no tile/type/summary loads and
# unconditional rejections (gas) leave the candidate set before the loop. Cell order, info flags and the one in-loop side effect
# (mux/muy on the hero's cell) are unchanged. Twin: -DNH_MOVEMENT_MASK_VERIFY (mfndpos_reference per call).
import shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'mt3'
dst=CS/'mt4/source'
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
        nh_move_set_bit(&level.move_columns[x + 1].gas, y, NH_SUMMARY(x, y).move_gas);""")
rep('src/mon.c',"""        if (domains & NH_MOVE_GAS) NH_SUMMARY(x, y).move_gas = 0;
    }""","""        if (domains & NH_MOVE_GAS) NH_SUMMARY(x, y).move_gas = 0;
    }
    for (x = 0; x < COLNO + 2; x++) {
        if (domains & NH_MOVE_PILES)
            level.move_columns[x].garlic = level.move_columns[x].boulder = level.move_columns[x].scare = 0;
        if (domains & NH_MOVE_TRAPS) level.move_columns[x].trap = 0;
        if (domains & NH_MOVE_GAS) level.move_columns[x].gas = 0;
    }""")
rep('src/mklev.c',"""    for (x = 0; x < COLNO; x++) {
        for (y = 0; y < ROWNO; y++) {
            nh_copy_terrain(&NH_TILE(x, y), &zerorm);""","""    nh_tile_clear_entities(NH_MOVE_PILES | NH_MOVE_TRAPS | NH_MOVE_GAS);
    for (x = 0; x < COLNO; x++) {
        for (y = 0; y < ROWNO; y++) {
            nh_copy_terrain(&NH_TILE(x, y), &zerorm);""")
# 4. the query
p=dst/'src/mon.c'; s=p.read_text()
a=s.index('static int mfndpos_masked(mon, poss, info, flag)'); b=s.index('\nint\nmfndpos(struct monst *mon', a)
fn=s[a:b]
# keep the per-call setup; take the reusable inner blocks from the original text
i_disp=fn.index('                int dispx, dispy;'); i_pile=fn.index('                if (NH_SUMMARY(nx, ny).move_pile & 2U) {')
inner_hero=fn[i_disp:i_pile].replace('                    if (MON_AT(nx, ny)) {','                    if (occ & cb) {')
i_trap=fn.index('                if (NH_SUMMARY(nx, ny).move_trap_present != 0) {'); i_poss=fn.index('                poss[cnt].x = nx;')
inner_trap=fn[i_trap:i_poss].replace('                if (NH_SUMMARY(nx, ny).move_trap_present != 0) {','                if (nb_trap & cb) {',1)
assert 'MON_AT' not in inner_hero and inner_hero.count('occ & cb')==1
fn=fn.replace("    unsigned int candidates, occupied;\n","    unsigned int candidates, occ, cb, nb_bars, nb_door, nb_pool, nb_lava, nb_db, nb_garlic, nb_boulder, nb_trap;\n    boolean rockcells, juiblex, origin_door, origin_door_diag, ispool, islava;\n",1)
i_next=fn.index('nexttry: /* eels prefer the water')
tail='''nexttry: /* eels prefer the water, but if there is no water nearby,
            they will crawl over land */
    if (mon->mconf) {
        flag |= ALLOW_ALL;
        flag &= ~NOTONL;
    }
    if (!mon->mcansee)
        flag |= ALLOW_SSM;
    cols = &level.move_columns[x];
#define NB(f) nh_move_neighbours(cols[0].f, cols[1].f, cols[2].f, y)
    rockcells = (flag & ALLOW_WALL) || rockok || treeok;
    candidates = rockcells ? nh_move_valid(x, y) : NB(nonrock);
    occ = NB(occupied);
    if (!(flag & (ALLOW_M | ALLOW_MDISP))
        && !SPWQ(mdat, SPW_DISPLACES, (mdat->mflags3 & M3_DISPLACES))
        && mdat != &mons[PM_PURPLE_WORM]) {
        /* Both hero positions stay on the original path. The old image may
           become obsolete during this loop, so keep the full checks below. */
        candidates &= ~(occ & ~(nh_move_position_bit(x, y, u.ux, u.uy)
                                | nh_move_position_bit(x, y, mon->mux, mon->muy)));
    }
    /* poison gas rejects a cell before any side effect: drop those cells now */
    if (!poisongas_ok && !in_poisongas)
        candidates &= ~NB(gas);
    nb_bars = NB(bars); nb_door = NB(door); nb_pool = NB(pool); nb_lava = NB(lava); nb_db = NB(dbridge);
    nb_garlic = NB(garlic); nb_boulder = NB(boulder); nb_trap = NB(trap);
    juiblex = Is_juiblex_level(&u.uz);
    origin_door = IS_DOOR(origin_typ);
    origin_door_diag = origin_door && (origin->rmflags & ~D_BROKEN);
    while (candidates) {
            bit = __builtin_ctz(candidates);
            candidates &= candidates - 1;
            cb = 1U << bit;
            nx = x - 1 + bit / 3;
            ny = y - 1 + bit % 3;
            cell = (const struct rm *) 0;
            if (rockcells) { /* rock may be a candidate: the original terrain logic */
                cell = nh_move_cell(nx, ny);
                cell_typ = TYP_AT(nx, ny);
                if (IS_ROCK(cell_typ)
                    && !((flag & ALLOW_WALL) && nh_cell_passwall(cell, nx, ny))
                    && !((IS_TREE(cell_typ) ? treeok : rockok) && nh_cell_dig(cell)))
                    continue;
            }
            /* KMH -- Added iron bars */
            if (nb_bars & cb) {
                if (!cell) cell = nh_move_cell(nx, ny);
                if (!(flag & ALLOW_BARS)
                    || ((cell->rmflags & W_NONDIGGABLE)
                        && (SPWQ(mdat, SPW_RUSTDMG, dmgtype(mdat, AD_RUST))
                            || SPWQ(mdat, SPW_CORRDMG, dmgtype(mdat, AD_CORR)))))
                    continue;
            }
            if (nb_door & cb) {
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
                    || ((nb_door & cb) && (cell->rmflags & ~D_BROKEN))
                    || ((origin_door || (nb_door & cb))
                        && mover.rogue)
                    /* mustn't pass between adjacent long worm segments,
                       but can attack that way */
                    || ((occ & nh_move_position_bit(x, y, x, ny)) && (occ & nh_move_position_bit(x, y, nx, y))
                        && worm_cross(x, y, nx, ny)
                        && !(occ & cb) && (nx != u.ux || ny != u.uy))))
                continue;
            ispool = (nb_pool & cb) != 0;
            islava = (nb_lava & cb) != 0;
            if (nb_db & cb) { /* drawbridge: depends on what is underneath */
                if (!cell) cell = nh_move_cell(nx, ny);
                if (!juiblex && (cell->rmflags & DB_UNDER) == DB_MOAT) ispool = TRUE;
                if ((cell->rmflags & DB_UNDER) == DB_LAVA) islava = TRUE;
            }
            if ((ispool == wantpool || poolok)
                && (lavaok || !islava)) {
''' + inner_hero + '''                if (nb_garlic & cb) {
                    if (flag & NOGARLIC) continue;
                    info[cnt] |= NOGARLIC;
                }
                if (nb_boulder & cb) {
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
#undef NB
    if (!cnt && wantpool && !nh_cell_pool(origin, x, y)) {
        wantpool = FALSE;
        goto nexttry;
    }
    return cnt;
}

'''
fn=fn[:i_next]+tail
s=s[:a]+fn+s[b:]
p.write_text(s)
print('mt4 source ready (base', BASE+'); query lines:', fn.count('\\n'))
