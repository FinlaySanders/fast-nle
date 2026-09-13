# Scoring a PufferLib NetHack policy on stock NLE

This note explains what the stock-NLE evaluation work adds to PufferLib and to the
`fast-nle` engine fork, and why it is built the way it is. The evaluation tooling lives
here, in `stock/` of the fast-nle repository, built by its own script from a PufferLib checkout
(`vendor/fast-nle/stock/`); PufferLib itself carries only the env behaviours and the training config. Written for a reviewer and for the article.

## 1. The problem

The NetHack policy in `ocean/nethack` trains on `fast-nle`, a fork of the NetHack
Learning Environment (NLE). The fork exists for speed (an order of magnitude faster
than NLE per step) and for a handful of extra observation channels that NLE's
observation does not carry but that a human player has for free: what terrain the
hero stands on, the price a shopkeeper quoted, which adjacent monsters are peaceful,
which spells are known, the pack's weight and the hero's carrying capacity, which
intrinsics the hero has, and the character's role, race and gender.

Every published NetHack agent score, and in particular AutoAscend's (median 5,336 in
the 2021 NetHack Challenge, 4,918 in the 2023 re-evaluation), was measured on stock
NLE through `NetHackChallenge-v0`: NLE's own observation, NLE's option string, random
character, one `env.step()` per keystroke, an episode cap of one million steps and an
abort after 10,000 steps without a game turn. A score on the fork is not comparable
to that. To claim a number against AutoAscend the same policy has to be run on
unmodified stock NLE, through the same interface, and the fork-only channels have to
come from somewhere legitimate.

The design constraint that follows is the one everything else hangs on: **the
policy may only receive information a player could read off the screen at zero
cost.** On stock NLE that is enforced by construction, because nothing else is
available. On the fork it is a discipline the engine exports have to follow, and the
one place they did not (Section 6) cost a week of attribution work.

## 2. Architecture: one env, one policy, three engines

The env (`ocean/nethack/nethack.h`), its observation packer, its action masks and
the policy are identical in every configuration. They talk to the engine through the
fork's C API: `nle_start`, `nle_step`, `nle_obs_refresh`, `nle_end`, plus the
introspection hooks (`nle_terrain_underfoot`, `nle_shop_price`, `nle_peaceful_at`,
`nle_spells`, `nle_weight`, `nle_intrinsics`, `nle_identity`, and so on). That API is
the seam. Three backends implement it:

| rung | engine behind the seam | how the hooks are answered | seedable | speed |
|---|---|---|---|---|
| fork | `vendor/fast-nle`, linked | read out of engine memory | yes | ~30K steps/s per GPU |
| stock C | stock `libnethack.so`, one private copy per env | reconstructed (`nh_derive.h`) | yes | ~10K games/hour |
| gym | stock NLE inside `NetHackChallenge-v0` | reconstructed (`nh_derive.h`) | no, NLE seeds itself | ~20 games/hour/worker |

Putting the seam at the engine API rather than at the observation has three
consequences that turned out to matter.

- No env or policy code differs between rungs, so an equivalence failure is always an
  engine or reconstruction difference, never a masking or packing one.
- The stock C rung and the gym rung share every line above the transport, and we
  verified they emit the same key stream on a seeded game. The C rung is therefore a
  legitimate stand-in for the gym: it is seedable and runs 512 games in parallel, so it
  is the certification instrument. The gym rung is slow and unseedable, so it is the
  confirmation on the literal competition interface.
- The gym rung owns the environment loop the same way AutoAscend does (a wrapper
  around `env.step`, one env per process, the agent deciding the next key). We checked
  AutoAscend's published source before settling on this; there is no `act(obs)`
  interface to match, and inverting control would have bought nothing.

## 3. The reconstruction (`nh_derive.h`)

`nh_derive.h` rebuilds every fork-only hook from stock's public observation. It reads
only: the glyph map, `blstats`, the message line, the `misc` prompt flags, the tty
character rows, and the text that comes back from probe keystrokes. It is shared by
the C backend and the gym backend so both derive exactly the same values.

### Probes

Some information is on screen only on request. The reconstruction sends zero-time
keystrokes to fetch it, exactly as a player would: `;` farlook on a cell for a
monster's description (peaceful or not, the hero's own polymorphed form), `:` look
here for the floor pile, `#terrain` for the terrain under objects, `\` for the
discoveries list, `+` for known spells, `#attributes` for intrinsics when a message
implies one changed. Every probe is a real `env.step()` in the gym and is counted
against the challenge's step cap and its no-progress rule, so probes are rationed:
none while a prompt is open, while a count prefix is being typed, while blind or
hallucinating (a farlook while hallucinating draws from the display RNG and would
desynchronize the game), and re-looks only when a message or a redraw says the cell
changed. Probes produce their own messages, so the message the key itself produced
is saved before a probe and put back afterwards (Section 4).

### Memory

Several channels need state the screen no longer shows. The reconstruction keeps a
per-level memory of terrain, of floor piles it has seen, of engravings it wrote or
read, of the lit state of corridors, and of the appearance-to-type identifications it
has learned, with explicit invalidation rules (a message that says a stack was
dropped or eaten, the hero moving, sight returning after blindness, a fresh level).
Knowledge that a player has by heart comes from static tables generated from NLE's
own public data (`nh_tables.h`: object weights and classes, monster flags and sizes).

### Channel by channel

| hook | source on stock | residual mismatch against the fork's truth |
|---|---|---|
| identity (role, race, gender) | the welcome line, tokenised with the tty wrap newline treated as a space | 0 |
| terrain underfoot | glyph map, level memory, `#terrain` probe for covered cells | 0.017% |
| food / container underfoot | `:` look, pile memory | 0 |
| shop price, inside shop | shopkeeper quote messages, level memory | 0 |
| peaceful monsters | `;` farlook on adjacent and unique monsters, anger rules from hit messages | 0.017 to 0.03% |
| spells | `+` menu | exact except a bench-ordering case at turn 1 |
| weight, capacity | inventory text priced by appearance with the same rule the fork now uses; capacity from strength, constitution, wounded legs, polymorph form | 0 / 0.02% |
| intrinsics | gain and loss messages, `#attributes`, the polymorphed form's own resistances from the monster tables | 0.1 to 0.35% |
| hero tile | glyph map with the concealment rule the fork uses while blind or hallucinating | 0.1% |
| cast blocked | public hunger band and status conditions | 0 |

Mismatch is counted per hook query at every step boundary, over recorded corpora of
1.1 to 1.6 million boundaries played by the policies being certified.

### The bench

The reconstruction was made testable offline. The fork harness can record a game:
every key, every probe reply, every observation and the fork's own hook values at
every boundary. `nh_derive_replay` re-runs the derive header over such recordings with
no engine and prints the mismatch table above in seconds, with the first divergent
messages for any channel. That loop, record once and iterate offline, is what got the
channels from a few percent to exact; a live cert per fix would have taken an hour
each. The bench is also how the trimmed header in this PR was shown to be identical
to the development one: same recordings, same table, byte for byte. The bench itself
stays out of the tree; it needs the fork harness.

A recording made with one policy does not exercise another's failure modes. Weight
under hallucination and the wrapped welcome line of the one character whose title
overflows 80 columns both appeared only when a 2B policy was recorded. Record with the
policy you certify.

## 4. The stock C backend (`nh_stock_backend.c`)

The backend implements the fork's `nle_*` entry points over stock's. Its design
choices are all forced by one fact: stock NetHack is a single-game program full of
globals, and the vec runs 512 games in one process.

- **One engine copy per env.** The stock `libnethack.so` is read once, written into a
  memfd per env and `dlopen`ed from `/proc/self/fd` with `RTLD_LOCAL`. Each copy has
  its own globals, so 512 games coexist. Stock's own `nle_start`/`nle_step`/`nle_end`
  are called through the copy.
- **Crash isolation.** Stock NLE 0.9.0 has known in-engine faults (a boulder rolled out
  of bounds, among others; the fork fixed them, stock cannot be modified). Every engine
  call runs under a per-thread `sigsetjmp`; a fault ends that episode as a death and
  abandons the copy's coroutine rather than the process.
- **Coroutine stack.** Stock runs the game on a 64 KiB `fcontext` stack that overflows
  under this policy's throw and explosion cascades. The binary exports
  `create_fcontext_stack`, which the copies bind to, and hands out 256 KiB.
- **The top line across probes.** The env reads the message the key produced. Probes
  overwrite it. The backend saves the message before the boundary's probes and
  restores it after, and answers stock's interactive `getpos` cursor the way the fork's
  headless port does, including the `--More--` that follows.
- **Challenge accounting.** Every key, probe or action, increments a step counter; the
  episode ends at one million steps or 10,000 steps without a game turn, as
  `NetHackChallenge-v0` does. Clock-less key loops are also cut at one million keys by
  the reconstruction itself so the derive can never pre-empt NLE's rule.
- **Options.** NLE's own option string with a random character, passed verbatim as NLE
  passes it. `NH_STOCK_OPTIONS` overrides.
- **Clock.** Stock reads the wall clock and the challenge plays under the real one, so
  the backend leaves it alone by default. `NH_STOCK_FIXEDCLOCK=<unix seconds>` pins
  every game to one instant by redirecting the copies' `time` and `localtime` imports
  through their GOT; the engine image is untouched. This is how the calendar arms in
  Section 7 were run and how a stock eval is made reproducible.

`stock/build.sh` compiles the backend into a `libnethack.so` that exports the fork's `nle_*`
API; `stock/puffer_stock` runs the unmodified `puffer` binary with that library first on the
loader's path (the binary carries a RUNPATH, which `LD_LIBRARY_PATH` precedes), so PufferLib's
build is untouched and the fork engine is never loaded. The
development version of this file carried some forty diagnostic and ablation switches
(a replay-and-compare harness against recorded fork games, weight cross-checks against
the engine's own inventory, message censuses). The PR version keeps only the challenge
configuration. It was checked against the development binary on a seeded run in the
deterministic vec mode with the clock pinned on both sides: 411 games, all identical.

## 5. The gym backend (`nh_gym_backend.c`, `nh_gym_runner.c`, `nhc_agent.py`)

The gym rung is the same shape with the engine transport replaced by callbacks into
Python. `nhc_agent.py` creates `NetHackChallenge-v0`, wraps it so that anything other
than `reset` and `step` raises (conformance is checkable, not asserted), and loads
`libnhagent.so`, which contains the env, the reconstruction and the policy's CPU
forward pass. When the env calls `nle_step`, the backend calls back into Python, which
calls `env.step(key)` and returns NLE's observation; the derive's probe keystrokes go
through the same path. Every key the challenge counts is counted. Workers run
sequential episodes; results are pooled at equal episode counts per worker because a
worker that finished more games has finished shorter ones.

## 6. Engine changes in `fast-nle`: public-observation exports

The fork's hooks read engine memory, and reading engine memory is where a channel can
quietly become an oracle. The rule the exports now follow is the one stock imposes:
an export may carry what a player could read off the screen at zero cost, and nothing
else. Two commits on the fork apply it:

- **Weight by appearance.** `nle_weight` priced every item by its true type. For
  unidentified boots, gloves, helmets and gray stones the true types weigh differently
  (a luckstone weighs 10, a loadstone 500), so the weight channel identified them. It
  now prices an item by its true type only while its name is displayed, otherwise by
  its appearance's canonical type, which is exactly what stock's inventory glyph
  shows. This was the 2B policy's entire 13 percent loss on stock: injecting the true
  weight back into the stock run recovered all of it, and the four other suspected
  causes each measured zero.
- **Canonical glyphs for shared appearances.** Gems and worthless glass of the same
  colour, bag of holding and bag of tricks, tin and magic whistle, the gray stones: the
  description slot named the true type. Unidentified objects now map to the canonical
  twin of their description.
- **Engraving memory while blind.** The engraving flag reported the true engraving
  under a blind hero. It now reports what the hero last knew about that square (read,
  felt, written, or possibly smudged), and the truth only when sighted, since a sighted
  look is free.
- **Hero tile while blind or hallucinating.** Both conceal what is underfoot. The
  hallucination case also drew from the display RNG on every frame, which made replay
  impossible; concealing first fixed both.
- **Ring charges, trapped containers, prayer counter.** Hidden state removed from the
  export or masked until identified.
- **Eager identity mapping.** Every map cell reflects the discoveries list at each
  fill, matching stock's redraw behaviour rather than the fork's lazy one.

None of these change the golden determinism gate; the hooks are outside it. The old
1B policy scored the same on the new channel as on the old one (13,154 against 13,060),
and the 4B trained on the leaky channel loses under one percent when the oracle is
removed, so the exports were fixed without breaking existing checkpoints. Six new
lanes were then trained on the fixed engine: the two 1Bs came in 5.5 percent above the
leaky 1B and the 2Bs bracket the leaky 2B.

## 7. Env changes in `ocean/nethack`

- **Zero-time memory.** The challenge aborts a game after 10,000 steps without a game
  turn. A policy trained on the fork never met that rule and could sit in a free
  refusal loop (wielding while handless, kicking air). The env remembers the exact
  actions the engine refused for free since the world last changed, keyed on hero
  position, level and clock, and masks an action after its second identical
  zero-time refusal. The second-refusal rule exists because a fast hero legitimately
  gets one extra action per turn; masking on the first cost 8 percent. With it on,
  stock runs have zero aborts and score 5 percent above runs without it. It is on for
  stock evaluations (the backends set `NH_ZT_MASK=1`) and off in training, which is
  the configuration every certified policy trained under.
- **Form mask.** A handless polymorph refuses wield, throw, wear and engrave. The env
  reads the refusal text, masks those verbs, and clears the belief on the return
  message or after 100 game turns. The expiry exists because two thirds of revert
  messages print mid-key and only the first page survives, for the training env as for
  the stock one. An audit over 376 games found the mask wrongly on for two keys in a
  hundred thousand, and two no-mask 4B lanes scored level with masked ones; it is kept
  because the certified policies trained with it, and it can be ablated out later.
- **Cast gate.** The engine refuses a cast below a hunger counter of 10; the status
  line shows one word across 1 to 50. The gate now uses the public band.
- **Options.** NLE's autopickup set (`pickup_types:$?!/`, no corpse exception, NetHack's
  pile limit) is the default option string. It is what the challenge uses and what the
  certified policies trained with.
- **Per-episode log.** `NH_EPLOG` writes one line per finished episode in completion
  order (score, end reason, turn, worst clock-less run, role, race, gender, depth,
  killer) for the burn-in protocol and the behaviour census.

## 8. Measurement protocol and results

A 512-agent eval finishes short games first, so the first completed episodes are
biased low. Every certified number drops the first 4,000 completed episodes and
reports the next 6,000 or 10,000. Per-game scores are heavy-tailed (standard deviation
15 to 20 thousand for a strong policy); 480 gym games pin a median to about 13
percent, 4,000 to about 4 percent, which is why the gym samples are pooled to
thousands of games before they are quoted.

| policy | fork, fixed engine | stock C strict | NetHackChallenge-v0 gym |
|---|---|---|---|
| 4B, seeds 7 and 21 pooled | 20,140 / 10,442 (12,020 games) | 19,188 / 10,314 (8,010) | 19,199 / 10,316 (5,749) |
| fixed 2B s703 | 17,592 / 10,298 (10,000) | 17,247 / 10,114 (6,005) | 16,501 / 9,200 (480) |
| fixed 1B s701 | 14,365 / 8,941 (10,000) | 13,728 / 8,255 (6,003) | 14,008 / 9,434 (480) |
| AutoAscend | | | median 5,336 (2021), 4,918 / mean 8,556 (2023) |

Mean / median. The two stock interfaces agree with each other within noise on every
policy. Stock reads a few percent under the fork on the mean and level on the median.
Most of that residual is the calendar: stock NetHack reads the real clock, and these
runs were played under a new moon, mostly at night. With the clock pinned to one
neutral daytime date, three replicates of the 4B on the same seed read 20,519 / 10,838,
19,753 / 10,283 and 19,705 / 10,441 against the fork's 20,133 / 10,658: parity. The same
seed under the real clock, new moon at night, read 18,241 / 9,754. A stock number
carries its date.

## 9. What is deliberately not in the tree

The derive replay bench and the fork harness that records for it, the drone launch
scripts, the training ini files, the result logs, the CPU-versus-CUDA diff tools and
the campaign ledger. The reconstruction's known residuals are documented rather than
patched: a floor pile of 17 or more objects overflows NLE's window and loses its first
page (an interface limit), an invisible hero cannot farlook itself (`^X` would do it),
and a blessed potion of see invisible leaves no public trace. On the fork side,
`nle_peaceful_at` still answers for monsters the hero has not seen; it is measured at
0.017 percent of queries and left for the next engine round.

## 10. Training configuration

`config/nethack.ini` now carries the configuration every checkpoint in this work was
trained with, the winner of the second September sweep (4 layers, learning rate
7.2e-4, momentum 0.98, the reward coefficients in the file). The previous values were
the release commit's, which predated that sweep by a day.
