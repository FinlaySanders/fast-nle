from pathlib import Path
import shutil
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';shutil.copy2(p,r/'region28-before-mon.c');s=p.read_text()
a='''    poisongas_ok =
        ((nonliving(mdat) || is_vampshifter(mon) || breathless(mdat))
         || resists_poison(mon));
    in_poisongas = ((gas_reg = visible_region_at(x, y)) != 0
                    && gas_reg->glyph == gas_glyph);'''
b='''    poisongas_ok = TRUE;
    in_poisongas = FALSE;
    if (nh_cur->g_region_c_n_regions) {
        poisongas_ok =
            ((nonliving(mdat) || is_vampshifter(mon) || breathless(mdat))
             || resists_poison(mon));
        in_poisongas = ((gas_reg = visible_region_at(x, y)) != 0
                       && gas_reg->glyph == gas_glyph);
    }'''
assert s.count(a)==1;p.write_text(s.replace(a,b))
