# Per-key floor invalidation candidate: audit before application

The index stores only floor-list pointer order and coordinates. Item type/quantity/status are read live, not cached.

Topology hooks confirmed in current source: place_object after floor insertion; remove_object before extraction; splitobj when OBJ_FLOOR; replace_object when OBJ_FLOOR; restore/reset/save/mklev floor-list changes. These hooks remain in candidatekey22.

Other coordinate writes inspected: detection copies coordinates into contained/inventory objects; swallowed punishment ball/chain are OBJ_FREE; container tip/quantum observation writes the same coordinates for floor boxes; reviving floor corpses retains the location from get_obj_location; container rot moves contained objects. None establishes a missing floor-index mutation hook. Raw mutation search is key22-mutation-sites.txt; this review is not proof by itself.

Required before promotion: NLE_FOBJ_VERIFY compares every cached pointer/order/coordinate against live fobj list across keystrokes, plus exact recorded trajectories including level transitions, object creation/deletion and resets. Any mismatch is a failure; do not suppress the assertion. Keep original per-key invalidation if gain is absent or the mutation audit remains incomplete.
