# Line-level LL read misses per policy step, 2048-game share (retained source, -g twin)

Only lines with DLmr>0 are listed; line numbers count annotated source rows (call-edge rows excluded), so they match the file.

self-cost LL read misses accounted: 221.4 lines/step

file                 DLmr/step  share
mon.c                     37.7  17.0%
monmove.c                 27.7  12.5%
winrl.cc                  15.7   7.1%
display.c                 15.6   7.0%
nethack.h                 13.3   6.0%
isaac64.c                 10.1   4.5%
hack.c                     9.5   4.3%
vision.c                   9.2   4.2%
mthrowu.c                  7.2   3.2%
vault.c                    6.5   2.9%
invent.c                   6.0   2.7%
cmd.c                      4.7   2.1%
basic_string.h             4.7   2.1%
dungeon.c                  3.6   1.6%
string_fortified.h         3.5   1.6%
track.c                    3.2   1.4%
hack.h                     2.9   1.3%
apply.c                    2.9   1.3%

 DLmr/step D1mr/step  file:line  source
      9.46      24.2  monmove.c:804  nh_fobj_x[n] = o->ox; nh_fobj_y[n] = o->oy;
      7.82      29.2  mon.c:1968  if (MON_AT(nx, ny)) {
      7.61      39.0  mon.c:840  nmtmp = mtmp->nmon;
      6.72      27.5  mon.c:1738  || (!Is_juiblex_level(&u.uz) && (c->typ == MOAT
      6.31      25.4  winrl.cc:727  (otmp->dknown && objects[otmp->otyp].oc_name_known) ? 1 : 0;
      6.02      27.0  display.c:1616  if (gbuf_glyph[y][x] != glyph || iflags.use_background_glyph) {
      5.15      36.7  vault.c:1120  if (Has_contents(obj))
      4.69      33.7  mthrowu.c:1123  for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
      4.57       9.5  basic_string.h:223  { return _M_dataplus._M_p; }
      3.96      14.8  nethack.h:317  if ((gl >= 0 && gl < NETHACK_NUMMONS)
      3.86      21.3  monmove.c:1117  if (otmp->otyp == ROCK)
      3.38       9.0  string_fortified.h:29  return __builtin___memcpy_chk (__dest, __src, __len,
      3.13       8.0  monmove.c:801  for (o = fobj; o; o = o->nobj) {
      3.07      13.7  dungeon.c:1083  tmp.dlevel = dungeons[i].dunlev_ureached;
      2.91      13.0  mon.c:573  switch (TYP_AT(mtmp->mx, mtmp->my)) {
      2.81      11.3  track.c:51  if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x][y])
      2.63       7.0  nethack.h:655  if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
      2.61      19.5  hack.c:3229  if (otmp->oclass == COIN_CLASS)
      2.55       7.8  vision.c:761  && (lev->lit || (next_row[col] & TEMP_LIT))) {
      2.41      10.0  mon.c:1915  && (NH_SUMMARY(nx, ny).move_gas != 0))
      2.35      17.4  mthrowu.c:1124  if (otmp->otyp == type)
      2.32       7.8  emmintrin.h:1383  return (__m128i) ((__v8hi)__A > (__v8hi)__B);
      2.31       6.4  display.c:862  } else if ((mon = m_at(x, y)) != 0
      2.26      11.5  mon.c:1926  || (m_at(x, ny) && m_at(nx, y) && worm_cross(x, y, nx, ny)
      2.16       8.9  rnd.c:92  int r = (int) (isaac64_next_uint64(nle_rng_state(CORE)) % x);
      2.05       7.5  apply.c:767  if (otmp->otyp != LEASH || otmp->leashmon == 0)
      1.99      12.2  mon.c:1840  in_poisongas = (NH_SUMMARY(x, y).move_gas != 0) != 0;
      1.94       9.8  monmove.c:127  boolean already_saw_mon = !occupation ? 0 : canspotmon(mtmp);
      1.90       8.2  hack.h:585  ltyp = NH_TILE(x, y).typ;
      1.87       8.9  monmove.c:1130  if ((mtoo = m_at(xx, yy)) != 0
      1.84       7.0  movement_masks.h:28  | ((((middle << 1) >> y) & 7U) << 3)
      1.75       7.4  isaac64.c:158  return _ctx->r[--_ctx->n];
      1.65      13.1  hack.c:3231  otmp = otmp->nobj;
      1.62       5.9  nethack.h:747  int row = env->obj_mem[cell];
      1.57       7.6  display.c:896  if (lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
      1.56       6.5  winrl.cc:691  st[0] = (otmp->bknown && otmp->oclass != COIN_CLASS)
      1.44       5.3  monmove.c:1383  boolean canseeit = cansee(mtmp->mx, mtmp->my);
      1.39       6.2  invent.c:1234  for (otmp = level.objs[x][y]; otmp; otmp = otmp->nexthere)
      1.33       3.8  vision.c:2438  if (!is_clear(row, left)) {
      1.32       4.4  invent.c:513  for (n = 0, o = *olist; o; o = by_nexthere ? o->nexthere : o->nobj)
      1.28       8.8  vault.c:1119  for (obj = invent; obj; obj = obj->nobj)
      1.26       3.5  vision.c:2434  right_edge = right_ptrs[row][left];
      1.26       4.7  winrl.cc:128  if (!objects[obj].oc_name_known) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_id
      1.23       2.0  display.c:852  _map_location(x, y, 1); /* map the location */\
      1.21       3.2  vision.c:2630  left_edge = left_ptrs[row][right];
      1.09       3.6  mon.c:1895  cell_typ = TYP_AT(nx, ny);
      1.06       6.8  hack.c:2356  switch (rno = NH_TILE(x, y).roomno) {
      1.03       4.0  mon.c:1785  if (NH_SUMMARY(x, y).move_pile & 4U) return TRUE;
      0.97       6.5  steal.c:83  while (chain && chain->otyp != GOLD_PIECE)
      0.94       3.7  nethack.h:673  unsigned long long m = env->mon_bits[2 * row + half];
      0.93       4.4  monmove.c:871  return nh_fobj_ptr[i];
      0.92       5.3  mon.c:1320  if (objects[otyp].oc_material == SILVER && mon_hates_silver(mtmp)
      0.91       9.6  winrl.cc:120  return nle_appearance_canon[slot];
      0.89       4.5  isaac64.c:60  m[i]=y=m[lower_bits(x)]+a+b;
      0.86       2.9  monmove.c:902  boolean sawmon = canspotmon(mtmp); /* before it moved */
      0.86       4.4  isaac64.c:61  r[i]=b=m[upper_bits(y)]+x;
      0.85       3.3  hack.h:628  ltyp = TYP_AT(x, y);
      0.85       2.6  winrl.cc:328  && objects[glyph_to_obj(glyph)].oc_name_known)
      0.84       4.2  invent.c:1235  if (otmp->otyp == otyp)
      0.83       4.2  isaac64.c:64  m[i]=y=m[lower_bits(x)]+a+b;
      0.81       4.1  isaac64.c:65  r[i]=b=m[upper_bits(y)]+x;
      0.79       2.0  cmd.c:5826  }
      0.78       4.0  isaac64.c:68  m[i]=y=m[lower_bits(x)]+a+b;
      0.77       2.8  apply.c:766  for (otmp = invent; otmp; otmp = otmp->nobj) {
      0.76       3.9  isaac64.c:69  r[i]=b=m[upper_bits(y)]+x;
      0.75       2.0  winrl.cc:765  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
      0.74       1.5  display.c:803  mon = m_at(x, y);
      0.73       3.7  isaac64.c:72  m[i]=y=m[lower_bits(x)]+a+b;
      0.71       3.5  isaac64.c:59  a=~(a^a<<21)+m[i+ISAAC64_SZ/2];
      0.71       2.9  nethack.h:681  unsigned long long m = env->it_bits[2 * row + half];
      0.71       3.6  isaac64.c:73  r[i]=b=m[upper_bits(y)]+x;
      0.71       4.8  monmove.c:1045  && ((lepgold = findgold(mtmp->minvent))
      0.70       3.8  hack.c:2366  if (goodtype(rno))
      0.67       2.7  weapon.c:582  prop = objects[rwep[i]].oc_skill;
      0.66       1.9  vision.c:828  if ((old_row[col] & IN_SIGHT)
      0.65       2.7  isaac64.c:58  x=m[i];
      0.64       3.1  timeout.c:550  if ((upp->intrinsic & TIMEOUT) && !(--upp->intrinsic & TIMEOUT)) {
      0.60       2.0  winrl.cc:771  if (ttyDisplay && ttyDisplay->toplin == 1)
      0.60       1.9  invent.c:1371  if (obj->oclass == COIN_CLASS)
      0.59       3.5  detect.c:1770  if ((mtmp = m_at(x, y)) != 0 && !aflag) {

libc call edges by inclusive LL read misses (callee cost attributed to the calling source line):
 DLmr/step D1mr/step  caller file:line  => callee
      0.25       0.8  wintty.c:2269  => ./malloc/./malloc/malloc.c:free (639x)
      0.18       0.2  nle.c:518  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.07       0.2  topl.c:179  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (98,719x)
      0.05       0.9  pline.c:149  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (116,298x)
      0.03       0.5  pline.c:335  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (32,276x)
      0.01       0.0  topl.c:186  => ./malloc/./malloc/malloc.c:free (695x)
      0.01       0.1  string_fortified.h:29  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.01       0.0  engrave.c:90  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,712x)
      0.01       0.0  pline.c:418  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (3,158x)
      0.01       0.0  windows.c:991  => ./malloc/./malloc/malloc.c:free (345x)
      0.01       0.0  pline.c:347  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,720x)
      0.01       0.0  pline.c:162  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (116,298x)
      0.01       0.0  cmd.c:3705  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (8,340x)
      0.01       0.0  pline.c:362  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,073x)
      0.01       0.0  wintty.c:1623  => ./malloc/./malloc/malloc.c:free (6,877x)
      0.01       0.0  nh_ctx_gen.c:63  => ./malloc/./malloc/malloc.c:free (960x)
      0.01       0.0  options.c:1507  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (18,060x)
      0.01       0.1  objnam.c:2304  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (28,358x)
      0.00       0.0  nle.c:1223  => ./malloc/./malloc/malloc.c:free (15x)
      0.00       0.0  mondata.c:784  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,831x)
      0.00       0.0  engrave.c:126  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (896x)
      0.00       0.0  botl.c:1045  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  options.c:4546  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (983x)
      0.00       0.0  invent.c:561  => ./malloc/./malloc/malloc.c:free (7,296x)
      0.00       0.0  botl.c:1047  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  pline.c:387  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (304x)
      0.00       0.0  save.c:1183  => ./malloc/./malloc/malloc.c:free (518x)
      0.00       0.0  invent.c:3968  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,263x)
      0.00       0.0  botl.c:381  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,170x)
      0.00       0.0  nle.c:156  => ./malloc/./malloc/malloc.c:calloc (15x)
      0.00       0.1  objnam.c:2220  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (9,226x)
      0.00       0.0  topl.c:398  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (2,484x)
      0.00       0.0  dlb.c:207  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (3,173x)
      0.00       0.0  weapon.c:1181  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (961x)
      0.00       0.7  objnam.c:2214  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (131,826x)
      0.00       0.0  objnam.c:2081  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (7,978x)
      0.00       0.1  invent.c:1521  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (242,545x)
      0.00       0.0  unistd.h:28  => ./io/../sysdeps/unix/sysv/linux/read.c:read (9,302x)
      0.00       0.0  mondata.c:779  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,520x)
      0.00       0.0  wintty.c:2047  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (639x)

Owners of cost attributed to inlined header lines (file:function rows with DLmr/step >= 0.5):
      8.55      35.6  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs'2 [/puffertank/experiments/nethack-engine-scaling-202610
      2.32       7.8  /usr/lib/gcc/x86_64-linux-gnu/13/include/emmintrin.h:nh_fobj_next
      2.61       9.7  /puffertank/experiments/nethack-compact-state-20261008/engines/invwt_g/source/include/movement_masks.h:mfndpos_masked.lt
      2.50      12.6  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs [/puffertank/experiments/nethack-engine-scaling-20261010
      2.07       9.7  /puffertank/experiments/nethack-compact-state-20261008/engines/invwt_g/source/include/hack.h:m_move
      0.83       4.7  ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 [/usr/lib/x86_64-linux-gnu/libc.so.6]
      4.32       8.7  /usr/include/c++/13/bits/basic_string.h:nethack_rl::NetHackRL::update_inventory_method()
      1.73       6.2  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:nethack_rl::NetHackRL::fill_obs(nle_observation*)
      0.63       3.9  harness_incpack/source/ocean/nethack/nethack.h:puf_step [/puffertank/experiments/nethack-engine-scaling-20261010/harness
      1.10       3.3  harness_incpack/source/ocean/nethack/nethack.h:nethack_tile_claim [/puffertank/experiments/nethack-engine-scaling-202610
      0.80       2.5  /usr/include/c++/13/bits/stl_vector.h:nethack_rl::NetHackRL::clear_nhwindow_method(int)
      1.18       2.2  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:step_one'2
