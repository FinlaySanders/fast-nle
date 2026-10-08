from pathlib import Path
import difflib,re
r=Path(__file__).parent;p=r/'engine-source/src/display.c';s=p.read_text();(r/'soa82-before-display.c').write_text(s)
a=s.index('typedef struct {\n    xchar new;');b=s.index('#define gbuf_start',a)
s=s[:a]+'''typedef struct {
    short glyph[ROWNO][COLNO];
    xchar fresh[ROWNO][COLNO];
} nle_glyph_buffer;
typedef char nle_glyph_fits_short[(MAX_GLYPH < 32768) ? 1 : -1];

static nle_glyph_buffer *
nle_gbuf_blob(void)
{
    if (!nh_cur->nh_lazy[15])
        nh_cur->nh_lazy[15] = calloc(1, sizeof(nle_glyph_buffer));
    return (nle_glyph_buffer *) nh_cur->nh_lazy[15];
}
#define gbuf_glyph (nle_gbuf_blob()->glyph)
#define gbuf_fresh (nle_gbuf_blob()->fresh)
'''+s[b:]
s=re.sub(r'gbuf\[([^]]+)\]\[([^]]+)\]\.glyph',r'gbuf_glyph[\1][\2]',s)
s=re.sub(r'gbuf\[([^]]+)\]\[([^]]+)\]\.new',r'gbuf_fresh[\1][\2]',s)
a=s.index('    register int x, y;',s.index('clear_glyph_buffer()'));b=s.index('    reset_glyph_bbox();',a)
s=s[:a]+'''    int x, y;
    nle_glyph_buffer *buf = nle_gbuf_blob();
    if (nh_cur->g_display_c_nul_gbuf_glyph == 0)
        nh_cur->g_display_c_nul_gbuf_glyph = cmap_to_glyph(S_stone);
    for (y = 0; y < ROWNO; y++)
        for (x = 0; x < COLNO; x++) {
            buf->glyph[y][x] = nh_cur->g_display_c_nul_gbuf_glyph;
            buf->fresh[y][x] = nh_cur->g_display_c_nul_gbuf_new;
        }
'''+s[b:]
a='''        register gbuf_entry *gptr = &gbuf[y][x = gbuf_start[y]];

        for (; x <= gbuf_stop[y]; gptr++, x++)
            if (gptr->new) {
                print_glyph(WIN_MAP, x, y, gptr->glyph, get_bk_glyph(x, y));
                gptr->new = 0;
            }'''
b='''        nle_glyph_buffer *buf = nle_gbuf_blob();
        for (x = gbuf_start[y]; x <= gbuf_stop[y]; x++)
            if (buf->fresh[y][x]) {
                print_glyph(WIN_MAP, x, y, buf->glyph[y][x], get_bk_glyph(x, y));
                buf->fresh[y][x] = 0;
            }''';assert s.count(a)==1;s=s.replace(a,b)
a='''    int x, y;
    for (y = 0; y < ROWNO; y++)
        for (x = 1; x < COLNO; x++)
            *dst++ = (short) gbuf_glyph[y][x];''';b='''    int y;
    nle_glyph_buffer *buf = nle_gbuf_blob();
    for (y = 0; y < ROWNO; y++) {
        memcpy(dst, &buf->glyph[y][1], (COLNO - 1) * sizeof(short));
        dst += COLNO - 1;
    }''';assert s.count(a)==1;s=s.replace(a,b)
assert 'gbuf_entry' not in s and 'gbuf[' not in s;p.write_text(s)
(r/'soa82.patch').write_text(''.join(difflib.unified_diff((r/'soa82-before-display.c').read_text().splitlines(True),s.splitlines(True),fromfile='a/src/display.c',tofile='b/src/display.c')))
