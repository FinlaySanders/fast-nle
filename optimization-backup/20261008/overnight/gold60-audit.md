# Prepared candidate60: persistent hero-gold absence

This is a follow-up to rejected gold51, not a retained change. Earlier scoped cache won1.37% score but lost2.21% depth. Hypothesis: eliminate per-key/per-monster-pass reset overhead and use a cold context byte, only invalidating on inventory mutation.

Only caches NULL; no object pointer or quantity is retained. findgold caches absence only when the input chain equals current invent; other chains preserve original scan. A NULL monster chain comparing equal to empty invent has the same NULL result.

Invalidation: common addinv added label before carry effects/update_inventory; direct inventory insertions in addinv/doorganize/reassign; reorder_invent before pure relinking; replace_object OBJ_INVENT before replacement; restore after restobjchn. Removals cannot invalidate known absence. splitobj cannot create first gold when none exists. reassign temporarily removes gold, but no function call or findgold query occurs before reinsertion; still conservatively invalidates on reinsertion.

Prior gold51 source audit covered direct ->otyp assignments: transforms of live existing objects do not create GOLD_PIECE in place; poly_obj uses replace_object, while mksobj creates unattached objects. This must be rechecked if pursued, and NLE_GOLD_VERIFY must scan actual inventory on every cache hit through full replay/fuzz. No correctness claim from this audit alone.

Candidate has been applied in isolated engine-source and frozen in pgo61-source. PGO59 finished/rejected before this edit.

## Follow-up source audit

Re-ran the complete direct otyp assignment search and saved gold60-otyp-assignments.txt. In-place live changes are fixed non-coin types, dragon-scale offsets, potion mixtures, or random choices confined to potion/wand/spellbook/gem ranges. Generic otyp assignments are mksobj construction and init_dummyobj, not mutation of live inventory into gold. Normal addinv paths all reach the added hook; merged stacks cannot introduce first gold into an inventory with no gold. Tail insertion reaches the hook before callbacks relevant to gold; optional auto-quiver applies only weapons/ammo.

Remaining requirement: diagnostic runtime cache checks and broad replay/fuzz before retaining. Static audit is evidence, not a complete behavioural proof.
