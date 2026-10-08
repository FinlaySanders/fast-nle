# Changed-row raw glyph cache audit (candidate, not retained)

The cached plane stores raw engine glyphs only. Every output call copies the full raw plane into the caller's buffer, so appearance/discovery remapping and underfoot overrides run as before and cannot contaminate the cache. No reliance on caller buffer identity.

Source writes to the private gbuf glyph payload are show_glyph and clear_glyph_buffer; the former invalidates that row, the latter all rows. newsym_force changes only the separate new flag and does not change glyph payload. Flush/row_refresh read glyphs and reset display dirty metadata, independently of the new cache validity.

Initial zero validity forces a full gather even before the first clear. Validity and plane are per-context, so context switches and fresh games do not share data. NLE_GLYPH_VERIFY independently compares every cached cell against the engine buffer at every copy. Existing glyph57_test.c can test random changes, clear/reset and interleaved contexts if the performance screen justifies it; it has not yet been run.
