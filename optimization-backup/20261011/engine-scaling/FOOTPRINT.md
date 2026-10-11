# Engine cache footprint (callgrind, retained engine, 512 games, warm 4096, measured 128 steps/game)

## share512: 2209 functions; per policy step: Dr 149,213 refs, D1mr 1,237, DLmr 37 lines (2.3 KB), DLmw 15
subsystem                Dr/step  D1mr/step  DLmr/step LL KB/step  share
monster movement          81,180      374.0       10.3       0.65  27.9%
other                     24,957      289.9        6.9       0.43  18.7%
obs export / tty          13,966      225.9        5.8       0.36  15.7%
floor objects              1,726       41.3        2.9       0.18   7.8%
display                    9,554       56.8        2.6       0.16   7.1%
vision                     3,929       31.1        2.4       0.15   6.5%
inventory weight           3,013       66.0        1.4       0.09   3.9%
harness                      115       15.7        1.4       0.09   3.8%
player movement            1,445       53.7        1.3       0.08   3.5%
rng                        3,772       37.8        1.1       0.07   3.0%
alloc/libc                   720       21.1        0.6       0.04   1.7%
other monster              3,253       22.6        0.1       0.01   0.3%
traps/engravings           1,584        1.3        0.0       0.00   0.1%

top functions by D1 read misses per step (lines touched beyond L1):
     174.5  monster movement   m_move
     112.6  monster movement   mfndpos_masked.lto_priv.0
      96.2  obs export / tty   fill_obs(nle_observation*)
      58.4  monster movement   movemon
      51.7  other              minliquid
      50.1  inventory weight   encumber_msg
      47.2  display            newsym
      47.0  obs export / tty   nethack_pack_obs'2
      40.1  floor objects      nh_fobj_next
      35.8  rng                isaac64_update.lto_priv.0
      34.2  player movement    domove_core
      22.9  obs export / tty   update_blstats()
      22.1  other              moveloop'2
      20.5  other monster      mcalcdistress
      20.3  other              gethungry
      18.8  vision             vision_recalc
      17.7  player movement    flush_screen
      16.3  obs export / tty   nethack_pack_obs
      16.1  other              set_uasmon
      15.4  obs export / tty   nle_weight

top functions by LL read misses per step:
       4.9  monster movement   mfndpos_masked.lto_priv.0
       4.0  monster movement   m_move
       2.7  floor objects      nh_fobj_next
       2.4  display            newsym
       2.1  obs export / tty   fill_obs(nle_observation*)
       1.4  obs export / tty   rl_inventory_item*)
       1.1  vision             vision_recalc
       1.0  player movement    domove_core
       1.0  harness            step_at'2
       1.0  inventory weight   encumber_msg
       0.9  rng                isaac64_update.lto_priv.0
       0.8  obs export / tty   nethack_pack_obs'2
       0.8  monster movement   movemon
       0.7  other              minliquid
       0.6  vision             right_side'2
       0.5  obs export / tty   nethack_pack_obs
       0.4  vision             left_side'2
       0.4  other              moveloop'2
       0.4  other              rhack'2
       0.3  obs export / tty   nle_weight
       0.3  harness            step_at
       0.3  monster movement   dochug
       0.2  other              xname_flags.lto_priv.0
       0.2  alloc/libc         __strlen_avx2
       0.2  other              select_rwep

## share2048: 2207 functions; per policy step: Dr 149,228 refs, D1mr 1,224, DLmr 285 lines (17.8 KB), DLmw 104
subsystem                Dr/step  D1mr/step  DLmr/step LL KB/step  share
monster movement          81,180      367.9       80.6       5.03  28.2%
obs export / tty          13,966      224.3       62.4       3.90  21.9%
other                     24,972      286.8       52.3       3.27  18.3%
inventory weight           3,013       65.6       17.6       1.10   6.2%
floor objects              1,726       41.1       17.3       1.08   6.1%
player movement            1,445       53.5       14.8       0.92   5.2%
display                    9,554       56.1       14.5       0.91   5.1%
vision                     3,929       30.9        9.8       0.61   3.4%
rng                        3,772       37.2        9.3       0.58   3.2%
harness                      115       15.7        3.5       0.22   1.2%
alloc/libc                   720       21.0        2.4       0.15   0.9%
traps/engravings           1,584        1.3        0.4       0.03   0.2%
other monster              3,253       22.1        0.4       0.03   0.2%

top functions by D1 read misses per step (lines touched beyond L1):
     172.8  monster movement   m_move
     111.7  monster movement   mfndpos_masked.lto_priv.0
      96.1  obs export / tty   fill_obs(nle_observation*)
      55.7  monster movement   movemon
      50.8  other              minliquid
      49.8  inventory weight   encumber_msg
      46.6  obs export / tty   nethack_pack_obs'2
      46.6  display            newsym
      40.0  floor objects      nh_fobj_next
      35.3  rng                isaac64_update.lto_priv.0
      34.1  player movement    domove_core
      22.2  obs export / tty   update_blstats()
      21.8  other              moveloop'2
      20.2  other              gethungry
      20.0  other monster      mcalcdistress
      18.6  vision             vision_recalc
      17.5  player movement    flush_screen
      16.3  obs export / tty   nethack_pack_obs
      16.2  other              set_uasmon
      15.3  obs export / tty   nle_weight

top functions by LL read misses per step:
      34.7  monster movement   m_move
      29.4  monster movement   mfndpos_masked.lto_priv.0
      28.6  obs export / tty   fill_obs(nle_observation*)
      16.7  floor objects      nh_fobj_next
      12.9  display            newsym
      12.6  obs export / tty   nethack_pack_obs'2
      12.4  inventory weight   encumber_msg
      12.4  player movement    domove_core
      10.3  monster movement   movemon
       8.6  other              minliquid
       8.4  rng                isaac64_update.lto_priv.0
       5.4  vision             vision_recalc
       4.9  obs export / tty   rl_inventory_item*)
       4.9  other              moveloop'2
       4.3  obs export / tty   nethack_pack_obs
       4.2  obs export / tty   nle_weight
       4.1  other              rhack'2
       3.3  obs export / tty   update_blstats()
       2.8  monster movement   dochug
       2.8  inventory weight   calc_capacity
       2.7  other              dosearch0
       2.2  inventory weight   update_inventory_method()
       2.2  monster movement   dochugw
       2.0  vision             right_side'2
       1.8  obs export / tty   nle_step

## extra LL read misses at the 2048-game share vs the 512-game share, by function (top 25)
      30.7  monster movement   m_move
      26.4  obs export / tty   fill_obs(nle_observation*)
      24.6  monster movement   mfndpos_masked.lto_priv.0
      14.0  floor objects      nh_fobj_next
      11.7  obs export / tty   nethack_pack_obs'2
      11.5  inventory weight   encumber_msg
      11.3  player movement    domove_core
      10.5  display            newsym
       9.6  monster movement   movemon
       7.9  other              minliquid
       7.5  rng                isaac64_update.lto_priv.0
       4.5  other              moveloop'2
       4.3  vision             vision_recalc
       3.9  obs export / tty   nle_weight
       3.8  other              rhack'2
       3.8  obs export / tty   nethack_pack_obs
       3.6  obs export / tty   rl_inventory_item*)
       3.1  obs export / tty   update_blstats()
       2.5  inventory weight   calc_capacity
       2.5  monster movement   dochug
       2.4  other              dosearch0
       2.0  monster movement   dochugw
       2.0  inventory weight   update_inventory_method()
       1.7  obs export / tty   nle_step
       1.6  player movement    flush_screen
