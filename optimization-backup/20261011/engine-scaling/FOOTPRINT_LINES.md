# Line-level LL read misses per policy step, 2048-game share (retained source, -g twin)

Only lines with DLmr>0 are listed; line numbers count annotated source rows (call-edge rows excluded), so they match the file.

self-cost LL read misses accounted: 294.7 lines/step

file                 DLmr/step  share
mon.c                     41.1  13.9%
monmove.c                 32.6  11.1%
hack.c                    28.1   9.5%
nethack.h                 21.0   7.1%
winrl.cc                  20.3   6.9%
string_fortified.h        17.3   5.9%
display.c                 16.5   5.6%
hack.h                    12.4   4.2%
isaac64.c                 12.1   4.1%
vision.c                  10.4   3.5%
mthrowu.c                  8.9   3.0%
cmd.c                      6.7   2.3%
nle.c                      6.1   2.1%
invent.c                   5.5   1.8%
basic_string.h             5.4   1.8%
track.c                    4.5   1.5%
dungeon.c                  3.7   1.2%
rnd.c                      3.3   1.1%

 DLmr/step D1mr/step  file:line  source
     17.71      51.4  nethack.h:645  if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
     17.13      46.9  string_fortified.h:29  return __builtin___memcpy_chk (__dest, __src, __len,
     14.06      59.1  hack.c:3120  if (otmp->oclass == COIN_CLASS)
     10.78      24.3  monmove.c:804  nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
     10.37      42.8  mon.c:829  nmtmp = mtmp->nmon;
      8.48      30.8  mon.c:1957  if (MON_AT(nx, ny)) {
      7.99      37.3  hack.h:582  ltyp = NH_TILE(x, y).typ;
      7.07      24.6  mon.c:1727  || (!Is_juiblex_level(&u.uz) && (c->typ == MOAT
      6.34      29.1  display.c:1616  if (gbuf_glyph[y][x] != glyph || iflags.use_background_glyph) {
      5.88      35.1  mthrowu.c:1123  for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
      5.56      23.5  hack.c:3122  else if (otmp->otyp != BOULDER || !throws_rocks(youmonst.data))
      5.26       9.6  basic_string.h:223  { return _M_dataplus._M_p; }
      4.67      13.6  winrl.cc:320  && objects[glyph_to_obj(glyph)].oc_name_known)
      4.61      22.7  monmove.c:1117  if (otmp->otyp == ROCK)
      4.46      13.7  winrl.cc:656  || is_weptool(otmp) || objects[otmp->otyp].oc_charged;
      4.24      17.0  hack.c:3124  otmp = otmp->nobj;
      4.21      15.4  hack.h:625  ltyp = TYP_AT(x, y);
      3.64      15.8  track.c:51  if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x][y])
      3.36       7.3  monmove.c:801  for (o = fobj; o; o = o->nobj) {
      3.34      12.3  rnd.c:92  int r = (int) (isaac64_next_uint64(nle_rng_state(CORE)) % x);
      3.00      10.5  mon.c:1904  && (NH_SUMMARY(nx, ny).move_gas != 0))
      2.99       8.4  vision.c:761  && (lev->lit || (next_row[col] & TEMP_LIT))) {
      2.94      18.3  mthrowu.c:1124  if (otmp->otyp == type)
      2.92       7.8  nle.c:727  base = objects[typ].oc_weight;
      2.75      11.2  dungeon.c:1083  tmp.dlevel = dungeons[i].dunlev_ureached;
      2.67       9.9  isaac64.c:158  return _ctx->r[--_ctx->n];
      2.66      13.1  mon.c:1829  in_poisongas = (NH_SUMMARY(x, y).move_gas != 0) != 0;
      2.54       6.9  display.c:862  } else if ((mon = m_at(x, y)) != 0
      2.51      12.5  mon.c:1915  || (m_at(x, ny) && m_at(nx, y) && worm_cross(x, y, nx, ny)
      2.41      11.0  monmove.c:127  boolean already_saw_mon = !occupation ? 0 : canspotmon(mtmp);
      2.23       6.7  emmintrin.h:1383  return (__m128i) ((__v8hi)__A > (__v8hi)__B);
      2.11       6.7  winrl.cc:686  (otmp->dknown && objects[otmp->otyp].oc_name_known) ? 1 : 0;
      2.07       9.5  monmove.c:1130  if ((mtoo = m_at(xx, yy)) != 0
      1.87       6.2  monmove.c:1383  boolean canseeit = cansee(mtmp->mx, mtmp->my);
      1.71       6.3  movement_masks.h:28  | ((((middle << 1) >> y) & 7U) << 3)
      1.65       6.1  invent.c:1232  for (otmp = level.objs[x][y]; otmp; otmp = otmp->nexthere)
      1.61       4.4  winrl.cc:128  if (!objects[obj].oc_name_known) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_id
      1.53      10.3  winrl.cc:120  return nle_appearance_canon[slot];
      1.45       3.9  vision.c:2630  left_edge = left_ptrs[row][right];
      1.34       2.0  display.c:852  _map_location(x, y, 1); /* map the location */\
      1.33       3.1  vision.c:2438  if (!is_clear(row, left)) {
      1.30       3.1  vision.c:2434  right_edge = right_ptrs[row][left];
      1.22       4.1  mon.c:1774  if (NH_SUMMARY(x, y).move_pile & 4U) return TRUE;
      1.20       3.5  mon.c:1884  cell_typ = TYP_AT(nx, ny);
      1.18       5.2  monmove.c:871  return nh_fobj_ptr[i];
      1.18       7.1  steal.c:83  while (chain && chain->otyp != GOLD_PIECE)
      1.09       3.0  monmove.c:902  boolean sawmon = canspotmon(mtmp); /* before it moved */
      1.06       2.0  cmd.c:5826  }
      1.06       3.8  isaac64.c:60  m[i]=y=m[lower_bits(x)]+a+b;
      1.04       5.4  mon.c:1309  if (objects[otyp].oc_material == SILVER && mon_hates_silver(mtmp)
      1.03       4.3  invent.c:1233  if (otmp->otyp == otyp)
      1.00       3.4  display.c:896  if (lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
      1.00       3.6  isaac64.c:61  r[i]=b=m[upper_bits(y)]+x;
      1.00       3.9  timeout.c:550  if ((upp->intrinsic & TIMEOUT) && !(--upp->intrinsic & TIMEOUT)) {
      0.98       5.3  monmove.c:1045  && ((lepgold = findgold(mtmp->minvent))
      0.96       3.4  isaac64.c:64  m[i]=y=m[lower_bits(x)]+a+b;
      0.93       3.3  isaac64.c:65  r[i]=b=m[upper_bits(y)]+x;
      0.91       2.0  winrl.cc:730  if (ttyDisplay && ttyDisplay->toplin == 1)
      0.90       4.4  hack.c:2366  if (goodtype(rno))
      0.90       3.2  isaac64.c:68  m[i]=y=m[lower_bits(x)]+a+b;
      0.87       3.1  isaac64.c:69  r[i]=b=m[upper_bits(y)]+x;
      0.85       2.0  winrl.cc:724  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
      0.84       2.0  vision.c:828  if ((old_row[col] & IN_SIGHT)
      0.84       3.0  isaac64.c:72  m[i]=y=m[lower_bits(x)]+a+b;
      0.81       2.9  isaac64.c:73  r[i]=b=m[upper_bits(y)]+x;
      0.81       1.5  display.c:803  mon = m_at(x, y);
      0.79       2.8  weapon.c:582  prop = objects[rwep[i]].oc_skill;
      0.78       2.0  light.c:275  if (DEADMONSTER(mon))
      0.72       3.1  detect.c:1751  if (NH_TILE(x, y).typ == SDOOR) {
      0.71       2.4  nle.c:730  if (otmp->oeaten) base /= 2;
      0.69       2.0  invent.c:1369  if (obj->oclass == COIN_CLASS)
      0.69       3.9  detect.c:1770  if ((mtmp = m_at(x, y)) != 0 && !aflag) {
      0.68       2.4  winrl.cc:680  | (otmp->greased ? 32 : 0)
      0.66       2.1  mkobj.c:2091  for (prev = (struct obj *) 0; curr; prev = curr, curr = curr->nobj) {
      0.66       2.1  mon.c:1897  && (((cell->rmflags & D_CLOSED) && !(flag & OPENDOOR))
      0.64       1.9  invent.c:1366  register struct obj *obj = level.objs[x][y];
      0.64       1.5  nethack.h:1155  long hx0 = env->blstats[NLE_BL_X], hy0 = env->blstats[NLE_BL_Y], hd0 = env->blstats[NLE_BL
      0.60       1.0  cmd.c:5008  }
      0.60       1.5  mapglyph.c:247  ch = showsyms[idx];
      0.60       3.1  monmove.c:1143  if (((likegold && otmp->oclass == COIN_CLASS)

libc call edges by inclusive LL read misses (callee cost attributed to the calling source line):
 DLmr/step D1mr/step  caller file:line  => callee
      0.26       0.8  wintty.c:2269  => ./malloc/./malloc/malloc.c:free (639x)
      0.18       0.2  nle.c:518  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.06       0.9  pline.c:149  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (116,298x)
      0.03       0.5  pline.c:335  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (32,276x)
      0.03       0.1  topl.c:179  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (98,719x)
      0.01       0.0  engrave.c:90  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,712x)
      0.01       0.0  topl.c:186  => ./malloc/./malloc/malloc.c:free (695x)
      0.01       0.0  pline.c:418  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (3,158x)
      0.01       0.0  windows.c:991  => ./malloc/./malloc/malloc.c:free (345x)
      0.01       0.0  pline.c:362  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,073x)
      0.01       0.0  cmd.c:3705  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (8,340x)
      0.01       0.0  nh_ctx_gen.c:63  => ./malloc/./malloc/malloc.c:free (960x)
      0.01       0.0  wintty.c:1623  => ./malloc/./malloc/malloc.c:free (6,877x)
      0.01       0.0  pline.c:347  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,720x)
      0.01       0.0  engrave.c:126  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (896x)
      0.01       0.0  nle.c:1223  => ./malloc/./malloc/malloc.c:free (15x)
      0.01       0.0  alloc.c:162  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (6,827x)
      0.01       0.0  mondata.c:784  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,831x)
      0.00       0.1  objnam.c:2304  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (28,358x)
      0.00       0.0  botl.c:1047  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  botl.c:1045  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  options.c:1507  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (18,060x)
      0.00       0.0  invent.c:1519  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (242,545x)
      0.00       0.0  save.c:1183  => ./malloc/./malloc/malloc.c:free (518x)
      0.00       0.0  options.c:4546  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (983x)
      0.00       0.0  pline.c:162  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (116,298x)
      0.00       0.0  nle.c:156  => ./malloc/./malloc/malloc.c:calloc (15x)
      0.00       0.0  invent.c:3966  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,263x)
      0.00       0.0  wintty.c:2003  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (3,484x)
      0.00       0.0  pline.c:387  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (304x)
      0.00       0.0  botl.c:381  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,170x)
      0.00       0.0  dlb.c:207  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (3,173x)
      0.00       0.0  unistd.h:28  => ./io/../sysdeps/unix/sysv/linux/read.c:read (9,302x)
      0.00       0.0  engrave.c:413  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (384x)
      0.00       0.0  objnam.c:4285  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (2,044x)
      0.00       0.1  objnam.c:2220  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (9,226x)
      0.00       0.7  objnam.c:2214  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (131,826x)
      0.00       0.0  mondata.c:779  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,520x)
      0.00       0.0  objnam.c:2081  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (7,978x)
      0.00       0.0  weapon.c:1181  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (961x)

Owners of cost attributed to inlined header lines (file:function rows with DLmr/step >= 0.5):
     13.75      46.7  /puffertank/experiments/nethack-cpu-scaling-20261008/cpu/source/ocean/nethack/nethack.h:nethack_pack_obs'2 [/puffertank/
      4.27      16.4  /puffertank/experiments/nethack-cpu-scaling-20261008/cpu/source/ocean/nethack/nethack.h:nethack_pack_obs [/puffertank/ex
      2.23       6.7  /usr/lib/gcc/x86_64-linux-gnu/13/include/emmintrin.h:nh_fobj_next
      2.40       8.4  /puffertank/experiments/nethack-compact-state-20261008/engines/footprint_g/source/include/movement_masks.h:mfndpos_maske
      9.14      41.1  /puffertank/experiments/nethack-compact-state-20261008/engines/footprint_g/source/include/hack.h:minliquid
      2.35       9.8  /puffertank/experiments/nethack-compact-state-20261008/engines/footprint_g/source/include/hack.h:m_move
     15.38      44.0  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:nethack_rl::NetHackRL::fill_obs(nle_observation*)
      0.95       4.7  ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 [/usr/lib/x86_64-linux-gnu/libc.so.6]
      4.96       8.7  /usr/include/c++/13/bits/basic_string.h:nethack_rl::NetHackRL::update_inventory_method()
      0.61       1.5  /puffertank/experiments/nethack-cpu-scaling-20261008/cpu/source/ocean/nethack/nethack.h:nethack_reward [/puffertank/expe
      0.96       3.6  /puffertank/experiments/nethack-cpu-scaling-20261008/cpu/source/ocean/nethack/nethack.h:puf_step [/puffertank/experiment
      1.36       3.2  /puffertank/experiments/nethack-cpu-scaling-20261008/cpu/source/ocean/nethack/nethack.h:nethack_tile_claim [/puffertank/
      0.93       2.5  /usr/include/c++/13/bits/stl_vector.h:nethack_rl::NetHackRL::clear_nhwindow_method(int)
      1.26       2.2  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:step_at'2
