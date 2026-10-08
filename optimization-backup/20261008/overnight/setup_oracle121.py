from pathlib import Path
from patch_pack121 import patch
r=Path(__file__).parent
s=patch((r/'pool83-control-source/ocean/nethack/nethack.h').read_text())
block=s[s.index('        int cell = 0;\n#if defined(__SSE2__)'):s.index('        for (; cell < NH_GRID; cell++)')]
block=block.replace('        int cell = 0;','int cell = 0; if(simd) {')+'}\n'
for a,b in [('env->glyphs','g'),('env->obj_mem','m'),('hero_cell','hero'),('mon_cell','mc'),('mon_g','mg'),('it_cell','ic'),('NH_GRID','N')]:block=block.replace(a,b)
import re
for a in ['nmon','nit']:block=re.sub(r'\b'+a+r'\b','(*'+a+')',block)
values={'NETHACK_GLYPH_CMAP_OFF':2359,'NETHACK_GLYPH_OBJ_LO':1906,'NETHACK_GLYPH_OBJ_HI':2359,'NETHACK_GLYPH_BODY_OFF':1144,'NETHACK_GLYPH_BODY_HI':1526}
for a,b in values.items():block=block.replace(a,str(b))
s=(r/'pack103-oracle.c').read_text()
start=s.index('for(int cell=0;cell<N;cell++){')
end=s.index(' int v=g[cell];',start)
s=s[:start]+block+'for(;cell<N;cell++){\n'+s[end:]
(r/'pack121-oracle.c').write_text(s)
