# Footprint by data structure (lines_misc1, 2048-game LL share; self cost of source lines)

lines beyond L1 per step (D1mr): 975 = 60.9 KB; LL read misses per step: 223.9

data structure                                       D1mr/step  KB/step  share  DLmr/step  share
object records (struct obj)                              211.1     13.2  21.7%      44.63  19.9%
unclassified                                             132.0      8.2  13.5%      27.83  12.4%
monster records (struct monst)                           116.4      7.3  11.9%      18.05   8.1%
obs buffers / packer (nethack.h, fill_obs writes)         86.7      5.4   8.9%      25.29  11.3%
display gbuf / screen                                     75.1      4.7   7.7%      19.40   8.7%
grid: terrain/location records                            62.8      3.9   6.4%      16.83   7.5%
RNG state (isaac64)                                       57.0      3.6   5.8%      14.19   6.3%
grid: monster map                                         51.8      3.2   5.3%      13.62   6.1%
grid: summary/pile/track planes                           49.8      3.1   5.1%      12.43   5.6%
hero/context scalars (u., flags., ctx)                    41.8      2.6   4.3%      10.46   4.7%
vision arrays                                             35.0      2.2   3.6%      11.37   5.1%
object-class table (objects[])                            32.5      2.0   3.3%       5.31   2.4%
floor-object index                                        11.3      0.7   1.2%       3.08   1.4%
harness (replay.c)                                         4.7      0.3   0.5%       0.36   0.2%
monster-class table (mons[])                               3.5      0.2   0.4%       0.89   0.4%
allocator / libc                                           3.1      0.2   0.3%       0.17   0.1%

largest unclassified lines (D1mr/step):
     9.5    0.97  winrl.cc:120  return nle_appearance_canon[slot];
     8.4    2.95  emmintrin.h:1383  return (__m128i) ((__v8hi)__A > (__v8hi)__B);
     7.2    0.00  botl.c:1016  fld = initblstats[i].fld;
     6.2    1.56  movement_masks.h:28  | ((((middle << 1) >> y) & 7U) << 3)
     4.4    0.00  botl.c:1024  fieldname = initblstats[i].fldname;
     4.0    0.79  hack.c:2366  if (goodtype(rno))
     2.8    0.87  monmove.c:943  boolean sawmon = canspotmon(mtmp); /* before it moved */
     2.8    0.67  timeout.c:550  if ((upp->intrinsic & TIMEOUT) && !(--upp->intrinsic & TIMEOUT)) {
     2.4    0.01  monmove.c:473  if (is_covetous(mdat))
     2.0    0.84  winrl.cc:765  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
     2.0    0.87  cmd.c:5826  }
     1.7    0.00  netlib.h:204  switch (verb) {
     1.6    0.39  allmain.c:265  if ((change == 1 && !Polymorph)
     1.5    0.44  eat.c:2991  if (saved_hs) {
     1.4    0.42  trap.c:5034  if (trap->tx == x && trap->ty == y)
     1.4    0.02  hacklib.c:740  if (!*s2)
     1.4    0.44  track.c:23  for (x = max(0, position->x - 1); x <= min(COLNO - 1, position->x + 1); x++)
     1.4    0.01  mapglyph.c:147  cmap_color(offset);
     1.3    0.29  spell.c:665  for (i = 0; i < MAXSPELL && spellid(i) != NO_SPELL; i++)
     1.3    0.42  stl_vector.h:1606  { _M_erase_at_end(this->_M_impl._M_start); }
     1.3    0.38  movement_masks.h:29  | ((((right << 1) >> y) & 7U) << 6)) & 0x1efU;
     1.3    0.33  monmove.c:1862  if (!(mvitals[PM_FOG_CLOUD].mvflags & G_GENOD) && is_vampshifter(mtmp)
     1.3    0.29  unique_ptr.h:199  pointer _M_ptr() const noexcept { return std::get<0>(_M_t); }
     1.2    0.46  cmd.c:5039  register const char *dp = index(Cmd.dirchars, sym);
     1.2    0.14  cmd.c:5974  sym = in_doagain ? pgetchar() : nh_poskey(&x, &y, &mod);
