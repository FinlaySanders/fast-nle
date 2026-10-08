# Typed-map token cache candidate120

Input key is exact full signed-short glyph array plus hero x/y. Cache is invalidated wherever object memory is cleared (reset and floor transition). No other code writes object memory. An unchanged glyph map makes its update idempotent; the capped cell lists and distance/tie order therefore repeat exactly. Cache contains private copies, so observation-buffer rebinding does not invalidate it.

Peacefulness may change without a glyph change. Every cache hit refreshes each non-padded monster token through the original read-only nle_peaceful_at hook, preserving pet short-circuit and detection/pet flags. Signed byte offsets reconstruct cell positions only for valid hero coordinates; invalid coordinates always fall back. Species+1 never zero for a populated token, so zero ID marks the original padded tail.

The stall watchdog still executes before the cache lookup, and all non-map observation fields and action-mask computation still execute. Engine, policy, RNG and macro action processing are unchanged. Reset invalidation occurs before the first packed observation. This reasoning requires replay and performance validation before retention.
