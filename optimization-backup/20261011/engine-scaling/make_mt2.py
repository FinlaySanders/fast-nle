# mt2 = <base> + species word: per-species predicate bits in a static table (built at library load; mons[] is const), used in the
# monster-turn pass instead of re-reading species flags; verify twin (-DNLE_SPW_VERIFY) compares every bit with the original macro.
# Also: m_move's pre-move canspotmon only when the monster is a vampshifter (its sole consumer).
import re,shutil,sys
from pathlib import Path
CS=Path('/puffertank/experiments/nethack-compact-state-20261008/engines')
BASE=sys.argv[1] if len(sys.argv)>1 else 'misc1'
dst=CS/'mt2/source'
if dst.parent.exists(): shutil.rmtree(dst.parent)
shutil.copytree(CS/BASE/'source',dst,symlinks=True)
PRED=[('tunnels','SPW_TUNNELS'),('needspick','SPW_NEEDSPICK'),('nohands','SPW_NOHANDS'),('verysmall','SPW_VERYSMALL'),('is_giant','SPW_GIANT'),
 ('is_covetous','SPW_COVETOUS'),('is_minion','SPW_MINION'),('is_rider','SPW_RIDER'),('is_unicorn','SPW_UNICORN'),('passes_walls','SPW_PASSWALL'),
 ('passes_bars','SPW_PASSBARS'),('is_human','SPW_HUMAN'),('is_undead','SPW_UNDEAD'),('throws_rocks','SPW_THROWSROCKS'),('hides_under','SPW_HIDESUNDER'),
 ('likes_gold','SPW_LIKEGOLD'),('likes_gems','SPW_LIKEGEMS'),('likes_objs','SPW_LIKEOBJS'),('likes_magic','SPW_LIKEMAGIC'),
 ('mindless','SPW_MINDLESS'),('is_animal','SPW_ANIMAL'),('is_mercenary','SPW_MERC'),('is_flyer','SPW_FLYER'),('is_floater','SPW_FLOATER'),
 ('is_clinger','SPW_CLINGER'),('is_swimmer','SPW_SWIMMER'),('likes_lava','SPW_LIKELAVA'),('nonliving','SPW_NONLIVING'),('breathless','SPW_BREATHLESS'),
 ('amorphous','SPW_AMORPHOUS'),('is_whirly','SPW_WHIRLY'),('unsolid','SPW_UNSOLID'),('webmaker','SPW_WEBMAKER'),('can_teleport','SPW_TPORT'),
 ('is_wanderer','SPW_WANDER'),('perceives','SPW_PERCEIVES'),('infravisible','SPW_INFRAVISIBLE'),('noattacks','SPW_NOATTACKS'),('is_watch','SPW_WATCH'),
 ('is_mind_flayer','SPW_MINDFLAYER'),('is_demon','SPW_DEMON')]
bits='\n'.join(f'#define {b} (1ULL << {i})' for i,(n,b) in enumerate(PRED))
extra_i=len(PRED)
EXTRA=[('SPW_DISPLACES','(((p)->mflags3 & M3_DISPLACES) != 0)'),('SPW_RUSTDMG','dmgtype((p), AD_RUST)'),('SPW_CORRDMG','dmgtype((p), AD_CORR)'),
 ('SPW_WEAPATTK','attacktype((p), AT_WEAP)'),('SPW_RANGED','ranged_attk((p))')]
bits+='\n'+'\n'.join(f'#define {b} (1ULL << {extra_i+i})' for i,(b,_) in enumerate(EXTRA))
header=f'''
/* Species word: every species-only predicate the monster turn asks, as bits of one 64-bit word per species.
 * mons[] is const, so the table is built once at library load. SPWQ(p, bit, orig) reads the bit; the verify
 * build also evaluates the original macro and reports any disagreement. */
{bits}
extern unsigned long long nh_spw[NUMMONS];
#ifdef NLE_SPW_VERIFY
#define SPWQ(p, bit, orig) ({{ const struct permonst *spw_p_ = (p); int spw_a_ = (nh_spw[spw_p_ - mons] & (bit)) != 0; \\
    int spw_b_ = (orig) != 0; if (spw_a_ != spw_b_) fprintf(stderr, "SPW_MISMATCH %s idx=%d\\n", #orig, (int) (spw_p_ - mons)); spw_b_; }})
#else
#define SPWQ(p, bit, orig) ((nh_spw[(const struct permonst *) (p) - mons] & (bit)) != 0)
#endif
'''
def rep(path,old,new,count=1):
    p=dst/path; s=p.read_text(); assert s.count(old)==count,(path,s.count(old),old[:70]); p.write_text(s.replace(old,new))
rep('include/hack.h',"#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))","#define nh_deepest_dirty() ((void) (nh_deepest_valid = 0))"+header)
# table + constructor in mondata.c
md=dst/'src/mondata.c'; s=md.read_text()
init='\n'.join(f'        if ({n}(p)) w |= {b};' for n,b in PRED)+'\n'+'\n'.join(f'        if ({expr.replace("(p)","p")}) w |= {b};' for b,expr in EXTRA)
s=s.rstrip()+f'''

unsigned long long nh_spw[NUMMONS];
static void __attribute__((constructor))
nh_spw_init(void)
{{
    int i;
    for (i = 0; i < NUMMONS; i++) {{
        const struct permonst *p = &mons[i];
        unsigned long long w = 0;
{init}
        nh_spw[i] = w;
    }}
}}
'''
md.write_text(s)
# slice-scoped replacements
def patch_slice(path,start_marker,end_marker,fn):
    p=dst/path; s=p.read_text(); a=s.index(start_marker); b=s.index(end_marker,a); seg=s[a:b]; new=fn(seg); p.write_text(s[:a]+new+s[b:]); return seg,new
ARG=r'((?:mdat|ptr|mtmp->data|mon->data|m->data|mtmp2->data|mtoo->data|m2->data))'
def sub_preds(seg):
    n=0
    for name,bit in PRED:
        seg,k=re.subn(r'\b'+name+r'\('+ARG+r'\)', lambda m: f'SPWQ({m.group(1)}, {bit}, {name}({m.group(1)}))', seg); n+=k
    seg,k=re.subn(r'\(mdat->mflags3 & M3_DISPLACES\)', 'SPWQ(mdat, SPW_DISPLACES, (mdat->mflags3 & M3_DISPLACES))', seg); n+=k
    seg,k=re.subn(r'dmgtype\(mdat, AD_RUST\)', 'SPWQ(mdat, SPW_RUSTDMG, dmgtype(mdat, AD_RUST))', seg); n+=k
    seg,k=re.subn(r'dmgtype\(mdat, AD_CORR\)', 'SPWQ(mdat, SPW_CORRDMG, dmgtype(mdat, AD_CORR))', seg); n+=k
    seg,k=re.subn(r'attacktype\(mdat, AT_WEAP\)', 'SPWQ(mdat, SPW_WEAPATTK, attacktype(mdat, AT_WEAP))', seg); n+=k
    seg,k=re.subn(r'\branged_attk\(mdat\)', 'SPWQ(mdat, SPW_RANGED, ranged_attk(mdat))', seg); n+=k
    print('  replacements:', n); return seg
print('mfndpos_masked'); patch_slice('src/mon.c','static int mfndpos_masked(mon, poss, info, flag)','\nint\nmfndpos(struct monst *mon', sub_preds)
print('nh_mover helpers'); patch_slice('src/mon.c','static inline boolean nh_mover_bad_rock(','/* return number of acceptable neighbour positions */', sub_preds)
print('dochug'); patch_slice('src/monmove.c','dochug(mtmp)\nregister struct monst *mtmp;\n{','\nshould_displace(mtmp, poss, info, cnt, gx, gy)', sub_preds)
print('m_move'); patch_slice('src/monmove.c','m_move(mtmp, after)\nregister struct monst *mtmp;','\nset_apparxy(mtmp)\nregister struct monst *mtmp;', sub_preds)
print('distfleeck+set_apparxy'); patch_slice('src/monmove.c','distfleeck(mtmp, inrange, nearby, scared)','\ndochug(mtmp)\nregister struct monst *mtmp;', sub_preds)
patch_slice('src/monmove.c','set_apparxy(mtmp)\nregister struct monst *mtmp;','    mtmp->mux = mx;\n    mtmp->muy = my;\n}', sub_preds)
# sawmon only matters on the vampshifter path
rep('src/monmove.c',"    boolean sawmon = canspotmon(mtmp); /* before it moved */","    boolean sawmon = is_vampshifter(mtmp) ? canspotmon(mtmp) : FALSE; /* before it moved; only the fog-cloud shift reads it */")
print('mt2 source ready (base', BASE+')')
