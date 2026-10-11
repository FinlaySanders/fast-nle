# Phase 3 — the monster turn: what it does, where the instructions go, how to make it substantially faster
(2026-10-10 late; numbers from the exact callgrind instruction census of the final stack, 512 mature games x 128 steps, per policy step)

## 1. What the subsystem does, per game turn
movemon() walks the monster chain once per game turn. For every monster that has movement budget it:
 1. pays the budget (mcalcmove assigned it earlier with an RNG-adjusted speed), re-runs vision if flagged, clears object bypasses,
 2. minliquid(): drowning/lava check from the tile under it,
 3. hiders/eels: re-hide checks (RNG), Conflict fights,
 4. dochugw() -> dochug(): the decision —
    a. wake-up / strategy flags / quest status; sleeping or frozen -> return,
    b. wipe_engr_at (engravings under it), small-probability unconfuse/unstun/teleport/regain-courage (RNG draws),
    c. set_apparxy(): where it thinks the hero is (perception + displacement, RNG when unseen),
    d. covetous tactics, distfleeck(): inrange/nearby/scared (distance, Elbereth/scare via onscary, sanctuary) -> possibly monflee (RNG),
    e. find_defensive/find_misc: item use scan over its inventory,
    f. blackmail / watchmen / mind-flayer specials, weapon wielding when close,
    g. if not adjacent (or fleeing/confused/peaceful/...): maybe cast a spell, then m_move(),
    h. otherwise attack (mattacku) — outside the redesign.
 5. m_move(): trapped?/eating?/hiding? early outs (RNG), set_apparxy again, species abilities (tunnel/open/unlock/bust),
    special movers (pets, shopkeepers, guards, priests, covetous, tengu), goal = believed hero position with approach/flee/random mode,
    tracking the hero's trail (gettrack) when it can't see, object attraction: a 5-radius box scan over the floor-object index for things it
    likes (gold/gems/objects/magic/rocks/hiding spots) with per-object filters, then the permission word (ALLOW_*) from ~12 species
    predicates, mfndpos(): the ordered candidate cells, should_displace(), the choice loop (recent-track avoidance with RNG, nearer/farther to
    goal, random tie-break with RNG), then act: attack/displace another monster, or move (place_monster, newsym, traps, pickup, doors, digging).
 6. mfndpos_masked(): for the up-to-8 neighbours (pre-filtered by column bitmasks for rock and occupancy): rock/tree/dig/passwall, bars,
    doors, gas, diagonal rules (doors, rogue level, long-worm crossing), pool/lava, Elbereth/scare/altar (nh_mover_scary), hero or image on
    the cell, other monster (aggression / displacement rights), temple sanctuary, garlic, boulders, hero line-of-fire (onlineu),
    tight diagonal squeeze, trap avoidance by species and trap memory -> poss[]/info[].
About 99 such monster moves happen per policy decision in mature games (several game turns per decision, 15-25 monsters per level).

## 2. Where the 405K instructions per step go (inclusive; the 555K step)
| part | self instr/step | per call (~96-99 calls) | nature |
|---|---|---|---|
| mfndpos_masked (+inlined helpers) | 90K | ~940 (~117/cell) | ~100 species predicates per call, ~15 small checks per cell, loop bookkeeping |
| m_move | 89K | ~900 | canspotmon 7K, permission word ~12K, mtrack loop 3K, choice loop 5K, object-scan setup, early outs |
| dochug + dochugw | 43K | ~440 | canspotmon 7K, flag checks, distfleeck/set_apparxy calls, item-use scans |
| nh_fobj_next (object scan) | 29K | | SSE scan of the floor index per monster with an object interest |
| distfleeck | 11K | ~110 | 2 dist2, perception, onscary; prologue/epilogue 4K |
| should_displace | 9K | ~95 | loop over candidates with MON_AT |
| mcalcmove, set_apparxy, mcalcdistress | 8K, 8K, 6K | | speed RNG, perception, per-turn status |
| minliquid, linedup, muse find_*, place_monster, mintrap, gettrack, dmonsfree | 2-7K each | | |
Observations: (1) no hotspot — the largest line is 7K (canspotmon) and the next 2.5K; (2) the SAME facts are recomputed 2-3x per move
(canspotmon in dochugw and m_move; "monster perceives hero" in distfleeck, set_apparxy and mfndpos; dist2 to the goal in distfleeck,
m_move and should_displace); (3) function prologues/epilogues of the small helpers are ~15K/step (2.7%) because LTO did not inline them;
(4) the species predicates are evaluated per call from the species table (~25 of them across the pass).

## 3. Why mt1 (terrain lookup table) was flat
The terrain checks it replaced were single compares; the whole terrain share of a cell is ~15 instructions. A table costs the same. Confirmed
natively (−0.2% / −0.5%) and by the census (see ir_compare lines_misc1 lines_mt1).

## 4. How to make it substantially faster — the restructure
Principle: every fact is computed once per (monster, turn) or once per (monster, species change), never per cell or per helper call;
the game's decision structure and every RNG draw stay exactly where they are.
 S1. Per-monster species word (uint32 in the 8 spare bytes of struct monst, keyed on the species index so it self-validates):
     tunnels/needspick, passes_walls/bars, amorphous, flyer/floater/clinger/swimmer, likes_lava, nonliving/breathless, nohands/verysmall,
     is_giant, minion/rider, unicorn, human/minotaur, undead(!ghost), throws_rocks, hides_under, can_track, covetous, likes_gold/gems/objs/magic,
     mindless/animal, msize class, webmaker/whirly/unsolid, resists via species, NODIAG. Replaces ~25 table-bit tests per move (~12K+10K).
 S2. Per-move fact record filled once at the top of dochugw and passed down (a struct on the stack, or a per-game "current mover" record):
     canspotmon, perceives-hero (mcansee && (!Invis || perceives)), dist2 to believed hero, inrange/nearby, mux/muy, in_poisongas,
     scary_immune, fog/squeeze. Removes the duplicate canspotmon (7K), the triple perception test, duplicate dist2s.
 S3. mfndpos_masked restructured around masks: fold gas, garlic/boulder, scary-pile, trap-present bits of the 3x3 neighbourhood into
     column bitmasks like nonrock/occupied, so cells that fail unconditional rules never enter the loop; precompute a per-species
     trap-avoid mask (which trap types this species avoids) so the trap block is one AND; compute the hero/image position bits once.
     Target ~117 -> ~60 instr/cell and ~100 -> ~20 per-call setup: 90K -> ~50K.
 S4. m_move: permission word from S1 (one OR of masks), choice loop with the track check as a 9-bit mask of recent positions
     (same RNG draws in the same order), should_displace merged into the single candidate pass (same results), object scan gated by a
     per-column "any object" mask over the 5-radius box (bit-exact: only skips when the box is empty; otherwise unchanged order).
 S5. Inline the per-move helpers (distfleeck, set_apparxy, should_displace, dochugw) into the pass to remove ~15K of call overhead;
     keep them as functions for the verify twin.
 S6. movemon/mcalcmove/mcalcdistress: per-turn status loop — mostly RNG and flag updates; small gains only.
Budget: S1 ~20K, S2 ~15K, S3 ~40K, S4 ~25K, S5 ~15K => ~115K of 555K (−20%) if everything lands; a conservative landing is −12..15%.
Each step is an isolated engine with a twin: the twin computes the fact the old way at the point of use and compares (facts), or runs
the reference query (mfndpos), logging mismatches; corpus replay; quick gates; ABBA; full gate; instruction census for the realized budget.

## 5. What we will learn
Whether a game-rules subsystem written for one game can be made 2x cheaper per call without touching rules or RNG order; how much of
NetHack's per-move cost is fact re-derivation versus irreducible rule evaluation; and whether the per-species word pattern generalizes
(attacks, item use) if the first steps pay.
