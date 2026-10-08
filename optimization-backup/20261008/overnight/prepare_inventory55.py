from pathlib import Path
import shutil,difflib
r=Path(__file__).parent;p=r/'engine-source/win/rl/winrl.cc';s=p.read_text();shutil.copy2(p,r/'inventory55-before-winrl.cc')
a='''            st[7] = 0;
        }
        std::memset(obs->inv_state + i * NLE_INV_STATE_FIELDS, 0,
                    (NLE_INVENTORY_SIZE - i) * NLE_INV_STATE_FIELDS);
    }
    if (obs->inv_true_glyphs && !nle_partial) {'''
b='''            st[7] = 0;
            if (obs->inv_true_glyphs)
                obs->inv_true_glyphs[i] = st[6] ? GLYPH_OBJ_OFF + otmp->otyp : NO_GLYPH;
        }
        std::memset(obs->inv_state + i * NLE_INV_STATE_FIELDS, 0,
                    (NLE_INVENTORY_SIZE - i) * NLE_INV_STATE_FIELDS);
        if (obs->inv_true_glyphs)
            std::fill(obs->inv_true_glyphs + i,
                      obs->inv_true_glyphs + NLE_INVENTORY_SIZE, NO_GLYPH);
    }
    if (obs->inv_true_glyphs && !nle_partial && !obs->inv_state) {'''
assert s.count(a)==1;t=s.replace(a,b);p.write_text(t);(r/'inventory55.patch').write_text(''.join(difflib.unified_diff(s.splitlines(True),t.splitlines(True),fromfile='a/win/rl/winrl.cc',tofile='b/win/rl/winrl.cc')))
