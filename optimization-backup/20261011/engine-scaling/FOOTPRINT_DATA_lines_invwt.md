# Footprint by data structure (lines_invwt, 2048-game LL share; self cost of source lines)

lines beyond L1 per step (D1mr): 1082 = 67.6 KB; LL read misses per step: 221.4

data structure                                       D1mr/step  KB/step  share  DLmr/step  share
object records (struct obj)                              237.2     14.8  21.9%      39.71  17.9%
unclassified                                             133.9      8.4  12.4%      25.44  11.5%
monster records (struct monst)                           125.4      7.8  11.6%      16.10   7.3%
obs buffers / packer (nethack.h, fill_obs writes)         87.3      5.5   8.1%      23.03  10.4%
display gbuf / screen                                     80.7      5.0   7.5%      18.31   8.3%
grid: terrain/location records                            67.5      4.2   6.2%      15.83   7.2%
RNG state (isaac64)                                       61.4      3.8   5.7%      13.10   5.9%
grid: monster map                                         56.0      3.5   5.2%      13.47   6.1%
grid: summary/pile/track planes                           54.8      3.4   5.1%      11.54   5.2%
hero/context scalars (u., flags., ctx)                    54.2      3.4   5.0%      12.74   5.8%
floor-object index                                        40.1      2.5   3.7%      14.54   6.6%
vision arrays                                             37.6      2.3   3.5%      11.31   5.1%
object-class table (objects[])                            33.4      2.1   3.1%       4.92   2.2%
harness (replay.c)                                         4.9      0.3   0.5%       0.32   0.1%
monster-class table (mons[])                               3.7      0.2   0.3%       0.81   0.4%
allocator / libc                                           3.7      0.2   0.3%       0.22   0.1%

largest unclassified lines (D1mr/step):
     9.6    0.91  winrl.cc:120  return nle_appearance_canon[slot];
     7.8    2.32  emmintrin.h:1383  return (__m128i) ((__v8hi)__A > (__v8hi)__B);
     7.7    0.00  botl.c:1016  fld = initblstats[i].fld;
     7.0    1.84  movement_masks.h:28  | ((((middle << 1) >> y) & 7U) << 3)
     5.0    0.00  botl.c:1024  fieldname = initblstats[i].fldname;
     3.8    0.70  hack.c:2366  if (goodtype(rno))
     3.1    0.64  timeout.c:550  if ((upp->intrinsic & TIMEOUT) && !(--upp->intrinsic & TIMEOUT)) {
     2.9    0.86  monmove.c:902  boolean sawmon = canspotmon(mtmp); /* before it moved */
     2.6    0.01  monmove.c:473  if (is_covetous(mdat))
     2.0    0.75  winrl.cc:765  if (WIN_MESSAGE != WIN_ERR && wins[WIN_MESSAGE])
     2.0    0.79  cmd.c:5826  }
     1.8    0.00  netlib.h:204  switch (verb) {
     1.5    0.29  eat.c:2991  if (saved_hs) {
     1.5    0.35  track.c:23  for (x = max(0, position->x - 1); x <= min(COLNO - 1, position->x + 1); x++)
     1.4    0.34  trap.c:5034  if (trap->tx == x && trap->ty == y)
     1.4    0.51  mapglyph.c:247  ch = showsyms[idx];
     1.4    0.02  hacklib.c:740  if (!*s2)
     1.4    0.33  pickup.c:1635  if (oldcap < newcap) {
     1.4    0.02  mapglyph.c:147  cmap_color(offset);
     1.3    0.39  movement_masks.h:29  | ((((right << 1) >> y) & 7U) << 6)) & 0x1efU;
     1.3    0.30  monmove.c:1821  if (!(mvitals[PM_FOG_CLOUD].mvflags & G_GENOD) && is_vampshifter(mtmp)
     1.3    0.37  stl_vector.h:1606  { _M_erase_at_end(this->_M_impl._M_start); }
     1.3    0.26  unique_ptr.h:199  pointer _M_ptr() const noexcept { return std::get<0>(_M_t); }
     1.3    0.38  movement_masks.h:27  return ((((left << 1) >> y) & 7U)
     1.2    0.31  allmain.c:265  if ((change == 1 && !Polymorph)
