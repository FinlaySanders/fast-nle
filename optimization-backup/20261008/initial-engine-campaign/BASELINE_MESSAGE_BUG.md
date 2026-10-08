# Baseline score replay failure: uninitialised monster name

Original corpus: score-record/env00457.trace, episode25, policy decision131399. First failing event1129606, byte offset19239926, engine key115 (`s`, completing `20s`), reported TIME65714. Expected raw hash bytes027722586cf737e2; diagnostic replay producedf22a81ea2d43dbb3.

This reproduces with the frozen original production library AND fresh baseline library, using both v2 and v3 full-backend replayers. It is not introduced by the candidates or the refresh augmentation. See check457.json and its four logs.

The current raw message is `The leprechaun hits it. <garbage> suddenly disappears!`. In src/mhitm.c's AD_SGLD branch, local `buf` is populated only under `vis && canseemon(mdef)`. The following teleport/disappearance path uses it under `vis && couldspot && !canspotmon(magr)`, which does not require the victim to be visible. Thus a visible thief attacking an unseen victim can print uninitialised stack bytes. The theft-items/nymph branch has the analogous predicate mismatch and warrants a separate audit.

The diagnostic replay was deliberately allowed to continue past mismatches (NOT a passing verifier): exactly three hash mismatches occur, K/F/O for this one decision, then the remaining trace matches. Actions, later observations, rewards and termination still match. This strongly localises the discrepancy to the transient message. The original expected message bytes were not stored, only hashes, so do not claim a bytewise comparison with the original message.

No gameplay/message fix has been applied to the performance candidates. Such a fix would intentionally change an exported observation and must remain separate under the campaign's no-behaviour-change constraint. Do not silently normalise, suppress, or exclude this failure in correctness reports.

The full score augmentation aborted at this failure and score-record-v2 is incomplete, without a completion marker. The preselected32 timing streams do not include457; that selection predates discovery of the bug. They can be converted and verified independently for unchanged fixed-work timings while this all-corpus baseline failure remains reported. Full score corpus validation is NOT a pass.
