# Line-level LL read misses per policy step, 2048-game share (retained source, -g twin)

Only lines with DLmr>0 are listed; line numbers count annotated source rows (call-edge rows excluded), so they match the file.

self-cost LL read misses accounted: 208.7 lines/step

file                 DLmr/step  share
mon.c                     26.4  12.7%
winrl.cc                  21.6  10.4%
display.c                 19.7   9.5%
monmove.c                 16.7   8.0%
nethack.h                 12.7   6.1%
hack.c                    10.3   4.9%
isaac64.c                 10.2   4.9%
vision.c                   8.7   4.2%
movement_masks.h           8.4   4.0%
mthrowu.c                  7.1   3.4%
invent.c                   6.5   3.1%
steed.c                    4.8   2.3%
basic_string.h             4.7   2.2%
cmd.c                      4.4   2.1%
string_fortified.h         3.6   1.7%
track.c                    3.0   1.4%
hack.h                     2.7   1.3%
nle.c                      2.5   1.2%

 DLmr/step D1mr/step  file:line  source
      7.30      38.5  mon.c:841  nmtmp = mtmp->nmon;
      6.45      25.8  winrl.cc:727  (otmp->dknown && objects[otmp->otyp].oc_name_known) ? 1 : 0;
      5.68      26.6  display.c:1616  if (gbuf_glyph[y][x] != glyph || iflags.use_background_glyph) {
      5.62      23.7  display.c:896  if (lev->glyph == cmap_to_glyph(S_litcorr) && lev->typ == CORR)
      5.02      24.2  monmove.c:1164  if (otmp->otyp == ROCK)
      4.83      15.8  steed.c:767  if ((othermon = level.monsters[x][y]) != 0) {
      4.66      34.3  mthrowu.c:1123  for (otmp = mtmp->minvent; otmp; otmp = otmp->nobj)
      4.59      18.0  winrl.cc:691  st[0] = (otmp->bknown && otmp->oclass != COIN_CLASS)
      4.58       9.6  basic_string.h:223  { return _M_dataplus._M_p; }
      3.76      14.8  nethack.h:317  if ((gl >= 0 && gl < NETHACK_NUMMONS)
      3.54      13.6  mon.c:1797  if (NH_SUMMARY(x, y).move_pile & 4U) return TRUE;
      3.48       8.9  string_fortified.h:29  return __builtin___memcpy_chk (__dest, __src, __len,
      3.06      17.7  movement_masks.h:36  | ((((middle << 1) >> y) & 7U) << 3)
      3.05      12.8  movement_masks.h:35  return ((((left << 1) >> y) & 7U)
      2.82      22.4  hack.c:3229  if (otmp->oclass == COIN_CLASS)
      2.67       8.4  mon.c:1818  if (pl->gen && pl->gen == nh_plane_gen && pl->key == key) return pl->col;
      2.56      12.2  track.c:51  if (x >= 0 && x < COLNO && y >= 0 && y < ROWNO && !nh_track_near[x][y])
      2.53       7.8  vision.c:761  && (lev->lit || (next_row[col] & TEMP_LIT))) {
      2.49       7.0  nethack.h:655  if (env->obj_mem[cell]) env->obj_mem[cell] = 0; // bare floor shown: no object here
      2.41       9.8  rnd.c:92  int r = (int) (isaac64_next_uint64(nle_rng_state(CORE)) % x);
      2.34       6.4  display.c:862  } else if ((mon = m_at(x, y)) != 0
      2.33      17.8  mthrowu.c:1124  if (otmp->otyp == type)
      2.32      12.8  mon.c:574  switch (TYP_AT(mtmp->mx, mtmp->my)) {
      2.18      10.8  movement_masks.h:37  | ((((right << 1) >> y) & 7U) << 6)) & 0x1efU;
      2.02      12.1  mon.c:1884  in_poisongas = (NH_SUMMARY(x, y).move_gas != 0) != 0;
      1.96      10.0  monmove.c:133  boolean already_saw_mon = !occupation ? 0 : canspotmon(mtmp);
      1.92       7.9  isaac64.c:158  return _ctx->r[--_ctx->n];
      1.90      16.0  hack.c:3231  otmp = otmp->nobj;
      1.85       8.5  hack.h:643  ltyp = NH_TILE(x, y).typ;
      1.79       9.2  monmove.c:1177  if ((mtoo = m_at(xx, yy)) != 0
      1.49       5.9  nethack.h:747  int row = env->obj_mem[cell];
      1.48       6.4  invent.c:1234  for (otmp = level.objs[x][y]; otmp; otmp = otmp->nexthere)
      1.45       5.5  monmove.c:1434  boolean canseeit = cansee(mtmp->mx, mtmp->my);
      1.40       5.6  winrl.cc:689  otmp = otmp->nobj, ++i) {
      1.27       2.0  display.c:852  _map_location(x, y, 1); /* map the location */\
      1.26       4.7  winrl.cc:128  if (!objects[obj].oc_name_known) return GLYPH_OBJ_OFF + gem_canon(objects[obj].oc_descr_id
      1.25       3.8  emmintrin.h:1377  return (__m128i) ((__v16qs)__A > (__v16qs)__B);
      1.24       4.4  invent.c:513  for (n = 0, o = *olist; o; o = by_nexthere ? o->nexthere : o->nobj)
      1.17       3.6  vision.c:2438  if (!is_clear(row, left)) {
      1.16       3.4  vision.c:2630  left_edge = left_ptrs[row][right];
      1.10       7.8  hack.c:2356  switch (rno = NH_TILE(x, y).roomno) {
      1.10       3.3  vision.c:2434  right_edge = right_ptrs[row][left];
      1.05      19.2  winrl.cc:697  || is_weptool(otmp) || object_defaults[otmp->otyp].oc_charged;
      1.02       4.6  invent.c:1235  if (otmp->otyp == otyp)
      0.95       6.8  steal.c:83  while (chain && chain->otyp != GOLD_PIECE)
      0.92       2.3  mkobj.c:2109  for (prev = (struct obj *) 0; curr; prev = curr, curr = curr->nobj) {
      0.91       3.2  mon.c:1829  if (key & 4U) e &= ~c->gas;
      0.91       5.2  mon.c:1321  if (objects[otyp].oc_material == SILVER && mon_hates_silver(mtmp)
      0.90       3.7  nethack.h:673  unsigned long long m = env->mon_bits[2 * row + half];
      0.90       4.0  monmove.c:918  return nh_fobj_ptr[i];
      0.87       3.5  mon.c:1796  if (IS_ALTAR(TYP_AT(x, y)) && (m->data->mlet == S_VAMPIRE || is_vampshifter(mon))) return 
      0.86       4.1  isaac64.c:60  m[i]=y=m[lower_bits(x)]+a+b;
      0.85      10.8  winrl.cc:120  return nle_appearance_canon[slot];
      0.84       2.5  winrl.cc:328  && objects[glyph_to_obj(glyph)].oc_name_known)
      0.84       3.5  isaac64.c:58  x=m[i];
      0.83       4.0  isaac64.c:61  r[i]=b=m[upper_bits(y)]+x;
      0.83       2.2  invent.c:1371  if (obj->oclass == COIN_CLASS)
      0.82       3.1  winrl.cc:721  | (otmp->greased ? 32 : 0)
      0.81       4.3  hack.c:2366  if (goodtype(rno))
      0.81       3.9  isaac64.c:64  m[i]=y=m[lower_bits(x)]+a+b;
      0.79       3.8  isaac64.c:65  r[i]=b=m[upper_bits(y)]+x;
      0.77       2.8  apply.c:780  if (otmp->otyp == LEASH)
      0.76       3.7  isaac64.c:68  m[i]=y=m[lower_bits(x)]+a+b;
      0.76       2.0  winrl.cc:765  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
      0.74       2.9  mon.c:1963  && (((cell->rmflags & D_CLOSED) && !(flag & OPENDOOR))
      0.74       2.0  cmd.c:5826  }
      0.74       1.5  display.c:803  mon = m_at(x, y);
      0.73       3.6  isaac64.c:69  r[i]=b=m[upper_bits(y)]+x;
      0.73       2.9  nethack.h:681  unsigned long long m = env->it_bits[2 * row + half];
      0.71       3.4  isaac64.c:72  m[i]=y=m[lower_bits(x)]+a+b;
      0.70       2.0  winrl.cc:771  if (ttyDisplay && ttyDisplay->toplin == 1)
      0.69       3.3  hack.h:697  ltyp = TYP_AT(x, y);
      0.69       3.3  isaac64.c:73  r[i]=b=m[upper_bits(y)]+x;
      0.67       4.8  monmove.c:1092  && ((lepgold = findgold(mtmp->minvent))
      0.67       2.8  weapon.c:582  prop = objects[rwep[i]].oc_skill;
      0.66       3.1  isaac64.c:59  a=~(a^a<<21)+m[i+ISAAC64_SZ/2];
      0.66       3.4  monmove.c:1190  if (((likegold && otmp->oclass == COIN_CLASS)
      0.65       1.9  vision.c:828  if ((old_row[col] & IN_SIGHT)
      0.64       2.5  nle.c:730  if (otmp->oeaten) base /= 2;
      0.63       3.0  timeout.c:550  if ((upp->intrinsic & TIMEOUT) && !(--upp->intrinsic & TIMEOUT)) {

libc call edges by inclusive LL read misses (callee cost attributed to the calling source line):
 DLmr/step D1mr/step  caller file:line  => callee
      0.25       0.8  wintty.c:2269  => ./malloc/./malloc/malloc.c:free (639x)
      0.25       0.8  topl.c:179  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (98,719x)
      0.18       0.2  nle.c:518  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.17       0.4  objnam.c:979  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strncmp_avx2 (19,519x)
      0.05       0.9  pline.c:149  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (116,298x)
      0.05       0.1  objnam.c:2081  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (7,978x)
      0.03       0.5  pline.c:335  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (32,276x)
      0.03       0.1  string_fortified.h:36  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (47,79
      0.01       0.1  string_fortified.h:29  => ./string/../sysdeps/x86_64/multiarch/memmove-vec-unaligned-erms.S:__memcpy_avx_unaligned_erms (15x)
      0.01       0.0  topl.c:186  => ./malloc/./malloc/malloc.c:free (695x)
      0.01       0.0  engrave.c:90  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,712x)
      0.01       0.0  pline.c:347  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,720x)
      0.01       0.0  pline.c:362  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,073x)
      0.01       0.0  windows.c:991  => ./malloc/./malloc/malloc.c:free (345x)
      0.01       0.0  pline.c:418  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (3,158x)
      0.01       0.0  cmd.c:3705  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (8,340x)
      0.01       0.0  nh_ctx_gen.c:63  => ./malloc/./malloc/malloc.c:free (960x)
      0.01       0.0  wintty.c:1623  => ./malloc/./malloc/malloc.c:free (6,877x)
      0.01       0.0  pline.c:162  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (116,298x)
      0.00       0.0  nle.c:1223  => ./malloc/./malloc/malloc.c:free (15x)
      0.00       0.0  botl.c:1047  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  botl.c:1045  => ./malloc/./malloc/malloc.c:free (330x)
      0.00       0.0  options.c:1507  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (18,060x)
      0.00       0.0  save.c:1183  => ./malloc/./malloc/malloc.c:free (518x)
      0.00       0.0  mondata.c:784  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (4,831x)
      0.00       0.0  engrave.c:126  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (896x)
      0.00       0.0  invent.c:3968  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,263x)
      0.00       0.0  nle.c:156  => ./malloc/./malloc/malloc.c:calloc (15x)
      0.00       0.0  options.c:4546  => ./string/../sysdeps/x86_64/multiarch/strchr-avx2.S:__strchr_avx2 (983x)
      0.00       0.0  pline.c:387  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (304x)
      0.00       0.1  objnam.c:2220  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (9,226x)
      0.00       0.0  unistd.h:28  => ./io/../sysdeps/unix/sysv/linux/read.c:read (9,302x)
      0.00       0.0  weapon.c:1181  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (961x)
      0.00       0.2  invent.c:1478  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (6,043x)
      0.00       0.0  botl.c:381  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,170x)
      0.00       0.0  dlb.c:207  => ./string/../sysdeps/x86_64/multiarch/strcmp-avx2.S:__strcmp_avx2 (3,173x)
      0.00       0.0  mondata.c:779  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (1,520x)
      0.00       0.2  objnam.c:2304  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (28,358x)
      0.00       0.0  files.c:393  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (696x)
      0.00       0.0  pline.c:375  => ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 (207x)

Owners of cost attributed to inlined header lines (file:function rows with DLmr/step >= 0.5):
      8.03      35.7  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs'2 [/puffertank/experiments/nethack-engine-scaling-202610
      8.29      41.3  /puffertank/experiments/nethack-compact-state-20261008/engines/mt8_g/source/include/movement_masks.h:mfndpos_masked.lto_
      2.49      12.7  harness_incpack/source/ocean/nethack/nethack.h:nethack_pack_obs [/puffertank/experiments/nethack-engine-scaling-20261010
      1.25       3.8  /usr/lib/gcc/x86_64-linux-gnu/13/include/emmintrin.h:nh_fobj_next
      1.89      10.0  /puffertank/experiments/nethack-compact-state-20261008/engines/mt8_g/source/include/hack.h:m_move
      0.81       4.9  ./string/../sysdeps/x86_64/multiarch/strlen-avx2.S:__strlen_avx2 [/usr/lib/x86_64-linux-gnu/libc.so.6]
      4.35       8.7  /usr/include/c++/13/bits/basic_string.h:nethack_rl::NetHackRL::update_inventory_method()
      1.85       6.0  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:nethack_rl::NetHackRL::fill_obs(nle_observation*)
      0.61       4.0  harness_incpack/source/ocean/nethack/nethack.h:puf_step [/puffertank/experiments/nethack-engine-scaling-20261010/harness
      1.06       3.3  harness_incpack/source/ocean/nethack/nethack.h:nethack_tile_claim [/puffertank/experiments/nethack-engine-scaling-202610
      0.68       2.5  /usr/include/c++/13/bits/stl_vector.h:nethack_rl::NetHackRL::clear_nhwindow_method(int)
      1.17       2.2  /usr/include/x86_64-linux-gnu/bits/string_fortified.h:step_one'2
