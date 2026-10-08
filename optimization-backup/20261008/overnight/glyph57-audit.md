# Glyph-plane candidate audit

Not retained; screening underway.

The canonical display buffer is private to src/display.c, accessed via gbuf macro over per-context lazy allocation15. Search of display.c finds glyph writes in show_glyph (direct assignment) and clear_glyph_buffer (whole-entry assignment). newsym_force changes only dirty flag. flush_screen clears dirty flags; redraw/glyph_at only read glyphs. The compact short plane is per context and initially zero, matching calloc of the canonical buffer. show_glyph validates coordinates then updates both; clear updates every entry. It stores the same cast to short that nle_copy_glyphs formerly applied.

NLE_GLYPH_VERIFY compares every cell against the canonical gbuf on every export, before memcpy. This diagnostic is NOT enabled in the performance build. If screen warrants proceeding, run diagnostic complete replay plus raw observation checks and context/reset/interleaved golden/fuzz gates before retention.

Cost:3318 bytes per context (21*79*2), an additional short write on changed glyphs, a full plane fill on clear. Benefit sought: replace per-export strided gather with contiguous memcpy. No stale-observation assumption: canonical writes immediately update the mirror.

Potential concern: nle_copy_glyphs no longer itself forces lazy allocation15 when called before any screen use; mirror zeros match old calloc output, but initialization/reset/interleaving tests must cover this.
