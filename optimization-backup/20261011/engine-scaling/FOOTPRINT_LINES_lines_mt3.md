# Line-level LL read misses per policy step, 2048-game share (retained source, -g twin)

Only lines with DLmr>0 are listed; line numbers count annotated source rows (call-edge rows excluded), so they match the file.

self-cost LL read misses accounted: 194.9 lines/step

file                 DLmr/step  share
mon.c                     34.9  17.9%
winrl.cc                  21.2  10.9%
monmove.c                 15.9   8.1%
display.c                 15.1   7.8%
nethack.h                 12.6   6.4%
isaac64.c                  9.7   5.0%
vision.c                   8.6   4.4%
hack.c                     8.4   4.3%
mthrowu.c                  6.6   3.4%
invent.c                   6.3   3.2%
basic_string.h             4.5   2.3%
cmd.c                      4.2   2.2%
string_fortified.h         3.5   1.8%
track.c                    2.8   1.5%
hack.h                     2.7   1.4%
nle.c                      2.4   1.2%
emmintrin.h                2.4   1.2%
rnd.c                      2.0   1.0%

 DLmr/step D1mr/step  file:line  source
      7.16      27.6  mon.c:1969  if (MON_AT(nx, ny)) {
      6.87      35.9  mon.c:841  nmtmp = mtmp->nmon;
      6.42      25.6  winrl.cc:727  (otmp->dknown && objects[otmp->otyp].oc_name_known) ? 1 : 0;
      6.17      25.5  mon.c:1739  || (!Is_juiblex_level(&u.uz) && (c->typ == MOAT
      5.91      25.1  display.c:1616  if (gbuf_glyph[y][x] != glyph || iflags.use_background_glyph) {
      4.71      22.9  monmove.c:1164  if (otmp->otyp == ROCK)
      4.45       9.6  basic_string.h:223  { return _M_dataplus._M_p; }
      4.40      31.9  mthrowu.c:1123  for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
      4.31      17.9  winrl.cc:691  st[0] = (otmp->bknown && otmp->oclass != COIN_CLASS)
      3.68      14.8  nethack.h:317  if ((gl >= 0 && gl < NETHACK_NUMMONS)
      3.42       8.9  string_fortified.h:29  return __builtin___memcpy_chk (__dest, __src, __len,
      2.56      13.0  mon.c:574  switch (TYP_AT(mtmp->mx, mtmp->my)) {
      2.54      20.5  hack.c:3229  if (otmp->oclass == COIN_CLASS)
      2.52       7.0  nethack.h:655  if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
      2.49       7.4  vision.c:761  && (lev->lit || (next_row[col] & TEMP_LIT))) {
      2.45      10.8  track.c:51  if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x][y])
      2.36       8.3  emmintrin.h:1383  return (__m128i) ((__v8hi)__A > (__v8hi)__B);
      2.35       9.1  mon.c:1916  && (NH_SUMMARY(nx, ny).move_gas != 0))
      2.22       6.0  display.c:862  } else if ((mon = m_at(x, y)) != 0
      2.14      16.5  mthrowu.c:1124  if (otmp->otyp == type)
      2.02      10.8  mon.c:1927  || (m_at(x, ny) && m_at(nx, y) && worm_cross(x, y, nx, ny)
      2.01       8.4  rnd.c:92  int r = (int) (isaac64_next_uint64(nle_rng_state(CORE)) % x);
      1.89      10.9  mon.c:1841  in_poisongas = (NH_SUMMARY(x, y).move_gas != 0) != 0;
      1.72       7.5  hack.h:643  ltyp = NH_TILE(x, y).typ;
      1.72      14.2  hack.c:3231  otmp = otmp->nobj;
      1.65       8.3  monmove.c:1177  if ((mtoo = m_at(xx, yy)) != 0
      1.63       9.0  monmove.c:133  boolean already_saw_mon = !occupation ? 0 : canspotmon(mtmp);
      1.63       7.0  isaac64.c:158  return _ctx->r[--_ctx->n];
      1.49       7.3  display.c:896  if (lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
      1.49       5.9  nethack.h:747  int row = env->obj_mem[cell];
      1.42       6.1  invent.c:1234  for (otmp = level.objs[x][y]; otmp; otmp = otmp->nexthere)
      1.31       5.9  movement_masks.h:28  | ((((middle << 1) >> y) & 7U) << 3)
      1.28       4.7  winrl.cc:128  if (!objects[obj].oc_name_known) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_id
      1.27       2.0  display.c:852  _map_location(x, y, 1); /* map the location */\
      1.26       5.0  monmove.c:1430  boolean canseeit = cansee(mtmp->mx, mtmp->my);
      1.25       5.4  winrl.cc:689  otmp = otmp->nobj, ++i) {
      1.20       3.5  vision.c:2434  right_edge = right_ptrs[row][left];
      1.18       3.6  vision.c:2438  if (!is_clear(row, left)) {
      1.17       4.4  invent.c:513  for (n = 0, o = *olist; o; o = by_nexthere ? o->nexthere : o->nobj)
      1.10       3.0  vision.c:2630  left_edge = left_ptrs[row][right];
      1.06       5.3  monmove.c:918  return nh_fobj_ptr[i];
      1.03       3.7  mon.c:1786  if (NH_SUMMARY(x, y).move_pile & 4U) return TRUE;
      1.01      19.5  winrl.cc:697  || is_weptool(otmp) || object_defaults[otmp->otyp].oc_charged;
      1.00       3.6  mon.c:1896  cell_typ = TYP_AT(nx, ny);
      0.99       4.4  invent.c:1235  if (otmp->otyp == otyp)
      0.92       2.3  mkobj.c:2109  for (prev = (struct obj *) 0; curr; prev = curr, curr = curr->nobj) {
      0.91       4.9  mon.c:1321  if (objects[otyp].oc_material == SILVER && mon_hates_silver(mtmp)
      0.90       3.7  nethack.h:673  unsigned long long m = env->mon_bits[2 * row + half];
      0.89       6.4  steal.c:83  while (chain && chain->otyp != GOLD_PIECE)
      0.88       5.9  hack.c:2356  switch (rno = NH_TILE(x, y).roomno) {
      0.87       4.2  isaac64.c:60  m[i]=y=m[lower_bits(x)]+a+b;
      0.87       9.7  winrl.cc:120  return nle_appearance_canon[slot];
      0.85       2.5  winrl.cc:328  && objects[glyph_to_obj(glyph)].oc_name_known)
      0.84       4.1  isaac64.c:61  r[i]=b=m[upper_bits(y)]+x;
      0.82       3.9  isaac64.c:64  m[i]=y=m[lower_bits(x)]+a+b;
      0.82       2.1  invent.c:1371  if (obj->oclass == COIN_CLASS)
      0.79       3.8  isaac64.c:65  r[i]=b=m[upper_bits(y)]+x;
      0.78       3.3  hack.h:688  ltyp = TYP_AT(x, y);
      0.78       3.5  isaac64.c:59  a=~(a^a<<21)+m[i+ISAAC64_SZ/2];
      0.76       3.7  isaac64.c:68  m[i]=y=m[lower_bits(x)]+a+b;
      0.76       3.0  winrl.cc:721  | (otmp->greased ? 32 : 0)
      0.74       3.6  isaac64.c:69  r[i]=b=m[upper_bits(y)]+x;
      0.74       2.0  cmd.c:5826  }
      0.73       2.8  apply.c:780  if (otmp->otyp == LEASH)
      0.72       1.4  display.c:803  mon = m_at(x, y);
      0.71       3.5  isaac64.c:72  m[i]=y=m[lower_bits(x)]+a+b;
      0.71       2.0  winrl.cc:765  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
      0.71       2.9  nethack.h:681  unsigned long long m = env->it_bits[2 * row + half];
      0.70       3.4  isaac64.c:73  r[i]=b=m[upper_bits(y)]+x;
      0.69       4.2  hack.c:2366  if (goodtype(rno))
      0.65       2.6  weapon.c:582  prop = objects[rwep[i]].oc_skill;
      0.63       4.5  monmove.c:1092  && ((lepgold = findgold(mtmp->minvent))
      0.61       2.5  nle.c:730  if (otmp->oeaten) base /= 2;
      0.60       3.2  monmove.c:1190  if (((likegold && otmp->oclass == COIN_CLASS)
      0.59       1.8  invent.c:1368  register struct obj *obj = level.objs[x][y];
      0.59       2.6  isaac64.c:58  x=m[i];
      0.57       1.8  vision.c:828  if ((old_row[col] & IN_SIGHT)
      0.56       2.1  mhitu.c:890  if ((o->owornmask & W_ARMOR) != 0L) {
      0.55       2.0  winrl.cc:771  if (ttyDisplay && ttyDisplay->toplin == 1)
      0.54       2.1  mon.c:1909  && (((cell->rmflags & D_CLOSED) && !(flag & OPENDOOR))

libc call edges by inclusive LL read misses (callee cost attributed to the calling source line):
 DLmr/step D1mr/step  caller file:line  => callee
      0.24       0.8  wintty.c:2269  => ./malloc/./malloc/malloc.c:free (639x)
      0.18       0.2  nle.c:518  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.07       0.1  objnam.c:2129  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (6,153x)
      0.06       0.7  pline.c:149  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (116,298x)
      0.03       0.1  objnam.c:2371  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,347x)
      0.03       0.5  pline.c:335  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (32,276x)
      0.03       0.1  string_fortified.h:36  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (47,79
      0.02       0.1  topl.c:179  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (98,719x)
      0.01       0.1  string_fortified.h:29  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.01       0.0  topl.c:186  => ./malloc/./malloc/malloc.c:free (695x)
      0.01       0.0  engrave.c:90  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,712x)
      0.01       0.0  pline.c:418  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (3,158x)
      0.01       0.0  windows.c:991  => ./malloc/./malloc/malloc.c:free (345x)
      0.01       0.0  pline.c:347  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,720x)
      0.01       0.0  cmd.c:3705  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (8,340x)
      0.01       0.2  timeout.c:1882  => ./malloc/./malloc/malloc.c:free (1,636x)
      0.01       0.0  nh_ctx_gen.c:63  => ./malloc/./malloc/malloc.c:free (960x)
      0.01       0.0  wintty.c:1623  => ./malloc/./malloc/malloc.c:free (6,877x)
      0.01       0.1  string_fortified.h:79  => ./string/../sysdeps/x86_64/multiarch/strcpy-avx2.S:__strcpy_avx2 (10,144x)
      0.01       0.0  pline.c:362  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,073x)
      0.01       0.0  nle.c:1223  => ./malloc/./malloc/malloc.c:free (15x)
      0.01       0.0  pline.c:162  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (116,298x)
      0.01       0.0  options.c:1507  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (18,060x)
      0.00       0.0  botl.c:1047  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  mondata.c:784  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,831x)
      0.00       0.0  botl.c:1045  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  engrave.c:126  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (896x)
      0.00       0.0  save.c:1183  => ./malloc/./malloc/malloc.c:free (518x)
      0.00       0.0  nle.c:156  => ./malloc/./malloc/malloc.c:calloc (15x)
      0.00       0.0  pline.c:375  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (207x)
      0.00       0.0  pline.c:387  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (304x)
      0.00       0.0  botl.c:381  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,170x)
      0.00       0.0  dlb.c:207  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (3,173x)
      0.00       0.7  objnam.c:2214  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (131,826x)
      0.00       0.0  unistd.h:28  => ./io/../sysdeps/unix/sysv/linux/read.c:read (9,302x)
      0.00       0.0  mondata.c:779  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,520x)
      0.00       0.0  weapon.c:1181  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (961x)
      0.00       0.1  objnam.c:2220  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (9,226x)
      0.00       0.0  topl.c:398  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (2,484x)
      0.00       0.0  invent.c:3968  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,263x)

Owners of cost attributed to inlined header lines (file:function rows with DLmr/step >= 0.5):
      7.87      35.6  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs'2 [/puffertank/experiments/nethack-engine-scaling-202610
      2.36       8.3  /usr/lib/gcc/x86_64-linux-gnu/13/include/emmintrin.h:nh_fobj_next
      1.91       8.2  /puffertank/experiments/nethack-compact-state-20261008/engines/mt3_g/source/include/movement_masks.h:mfndpos_masked.lto_
      2.53      12.6  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs [/puffertank/experiments/nethack-engine-scaling-20261010
      1.84       9.1  /puffertank/experiments/nethack-compact-state-20261008/engines/mt3_g/source/include/hack.h:m_move
      0.54       4.2  ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 [/usr/lib/x86_64-linux-gnu/libc.so.6]
      4.22       8.7  /usr/include/c++/13/bits/basic_string.h:nethack_rl::NetHackRL::update_inventory_method()
      1.80       6.0  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:nethack_rl::NetHackRL::fill_obs(nle_observation*)
      0.60       3.8  harness_incpack/source/ocean/nethack/nethack.h:puf_step [/puffertank/experiments/nethack-engine-scaling-20261010/harness
      1.04       3.3  harness_incpack/source/ocean/nethack/nethack.h:nethack_tile_claim [/puffertank/experiments/nethack-engine-scaling-202610
      0.73       2.5  /usr/include/c++/13/bits/stl_vector.h:nethack_rl::NetHackRL::clear_nhwindow_method(int)
      1.16       2.2  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:step_one'2
