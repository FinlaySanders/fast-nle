# Attribute the line-level footprint to DATA STRUCTURES (what a hot line touches), to size the structural legs.
# usage: footprint_data.py <label> <engine_g>   (reads callgrind.<label>.out.1 like footprint_lines.py)
import re,subprocess,sys,collections
from pathlib import Path
R=Path(__file__).resolve().parent; STEPS=512*128
LABEL=sys.argv[1]; ENGINE=sys.argv[2]
out=subprocess.run(['callgrind_annotate','--inclusive=no','--threshold=100','--show-percs=no','--auto=yes',str(R/('callgrind.'+LABEL+'.out.1'))],capture_output=True,text=True).stdout
RULES=[ # (class, regex on source text) first match wins
 ('obs buffers / packer (nethack.h, fill_obs writes)', r'env->|obs->|inv_state|inv_true_glyphs|blstats_|chars_|colors_|specials_|screen_descriptions|nle_copy_glyph_rows|maybe_true_glyph|std::memcpy|__memcpy_chk|memset|basic_string|_M_dataplus|inventory_|nethack_pack|mon_bits|it_bits|obj_mem'),
 ('display gbuf / screen', r'gbuf_glyph|gbuf_start|gbuf_stop|glyph_at|show_glyph|_map_location|lev->glyph|newsym|flush_screen|wintty|topl|cl_end|tty_'),
 ('vision arrays', r'viz_array|could_see|cansee\(|couldsee|left_ptrs|right_ptrs|next_row|clear_path|vision|is_clear\(|lev->lit|TEMP_LIT|seenv'),
 ('grid: terrain/location records', r'NH_TILE|TYP_AT|levl\[|level\.locations|lev->typ|->typ\b|c->typ|IS_ROOM|IS_WALL|closed_door|is_pool|is_lava|nh_typ_plane|roomno|doors\['),
 ('grid: monster map', r'MON_AT|m_at\(|level\.monsters|monat|mon_at'),
 ('grid: summary/pile/track planes', r'NH_SUMMARY|move_gas|move_pile|nh_pile|nh_track_near|track\[|gettrack|OBJ_AT|level\.objs\[|sobj_at|nh_trap|t_at\('),
 ('floor-object index', r'nh_fobj|fobj\b'),
 ('monster records (struct monst)', r'mtmp->|mtmp2->|mon->|mdef->|magr->|->nmon|->minvent|->mx|->my|->data\b|->mhp|->mtame|->mpeaceful|->mflee|DEADMONSTER|youmonst|->misc_worn_check|->mw\b|MON_WEP|fmon\b'),
 ('object records (struct obj)', r'Has_contents|contained_gold|otmp->|otmp2->|obj->|obj1->|obj2->|o->|->nobj|->nexthere|->owt|->otyp|->quan|->oclass|->ox|->oy|->cobj|->ocarry|->where|invent\b|uwep|uarm|uball|uchain|->oextra|->spe\b|->dknown|->bknown|->known\b|->cursed|->blessed|->oeroded|->owornmask|->opoisoned|->greased|->rknown|->leashmon'),
 ('object-class table (objects[])', r'objects\[|object_defaults\[|oc_name_known|oc_weight|oc_material|oc_class|oc_descr|is_weptool|objects\b'),
 ('monster-class table (mons[])', r'mons\[|->mlet|mlevel|mmove|mflags|nohands|verysmall|throws_rocks|tunnels|needspick|is_rider|likes_|hates_|resists_|passes_walls|amorphous|is_flyer|is_swimmer|is_clinger|likeobjs|likegold|likegems|likerock|likemagic'),
 ('RNG state (isaac64)', r'isaac64|_ctx->r\[|_ctx->n|lower_bits|upper_bits|rn2\(|rnd\(|rn1\(|rnl\(|nle_rng_state'),
 ('hero/context scalars (u., flags., ctx)', r'\bu\.|flags\.|iflags\.|context\.|program_state|moves\b|dungeons\[|u\.uz|Upolyd|Blind|Underwater|Levitation|Punished|nh_invwt|nh_hgold|nh_deepest|nh_leash|nh_invgen|nh_cur|multi\b|occupation'),
 ('allocator / libc', r'malloc|free\(|posix_memalign|strlen|strchr|strcmp|strcpy|Sprintf|sprintf|pline|vsnprintf|fprintf'),
 ('harness (replay.c)', r'replay\.c|step_at|rounds'),
]
comp=[(c,re.compile(rx)) for c,rx in RULES]
events=None; cur=None; lineno=0; rows=[]
for ln in out.splitlines():
    m=re.search(r'Events\s+shown:\s+(.*)',ln)
    if m: events=m.group(1).split(); continue
    m=re.match(r'^-- Auto-annotated source: (.*)$',ln)
    if m: cur=m.group(1).strip(); lineno=0; continue
    if not (cur and events): continue
    tok=ln.split()
    if len(tok)>len(events) and all(t=='.' or (t.replace(',','').isdigit()) for t in tok[:len(events)]):
        nums=[0 if t=='.' else int(t.replace(',','')) for t in tok[:len(events)]]; ev=dict(zip(events,nums)); txt=' '.join(tok[len(events):])
        if txt.startswith('=>'): continue
        if 'events annotated' in txt or 'Events annotated' in txt: continue
        lineno+=1
        if ev.get('D1mr',0)>0 or ev.get('DLmr',0)>0: rows.append((ev.get('DLmr',0),ev.get('D1mr',0),ev.get('Dr',0),Path(cur).name,lineno,txt))
    elif ln.startswith('-- line '):
        mm=re.match(r'^-- line (\d+)',ln); lineno=int(mm.group(1))-1 if mm else lineno
    elif ln.strip() and not ln.startswith('--'): lineno+=1
def classify(fname,txt):
    if fname=='replay.c': return 'harness (replay.c)'
    if fname in ('nethack.h',): return 'obs buffers / packer (nethack.h, fill_obs writes)'
    if fname in ('isaac64.c','rnd.c','nlernd.c'): return 'RNG state (isaac64)'
    if fname in ('vision.c',): return 'vision arrays'
    if fname in ('display.c','wintty.c','topl.c'): return 'display gbuf / screen'
    for c,rx in comp:
        if rx.search(txt): return c
    return 'unclassified'
by=collections.defaultdict(lambda:[0,0,0,0]); un=[]
for dl,d1,dr,f,n,txt in rows:
    c=classify(f,txt); by[c][0]+=dl; by[c][1]+=d1; by[c][2]+=dr; by[c][3]+=1
    if c=='unclassified' and d1>0: un.append((d1,dl,f,n,txt))
tot_dl=sum(v[0] for v in by.values()); tot_d1=sum(v[1] for v in by.values())
print(f'# Footprint by data structure ({LABEL}, 2048-game LL share; self cost of source lines)\n')
print(f'lines beyond L1 per step (D1mr): {tot_d1/STEPS:.0f} = {tot_d1/STEPS*64/1024:.1f} KB; LL read misses per step: {tot_dl/STEPS:.1f}\n')
print(f"{'data structure':52}{'D1mr/step':>10}{'KB/step':>9}{'share':>7}{'DLmr/step':>11}{'share':>7}")
for c,v in sorted(by.items(),key=lambda kv:-kv[1][1]):
    print(f"{c:52}{v[1]/STEPS:>10.1f}{v[1]/STEPS*64/1024:>9.1f}{v[1]/tot_d1*100:>6.1f}%{v[0]/STEPS:>11.2f}{v[0]/tot_dl*100:>6.1f}%")
print('\nlargest unclassified lines (D1mr/step):')
for d1,dl,f,n,txt in sorted(un,reverse=True)[:25]: print(f"{d1/STEPS:>8.1f}{dl/STEPS:>8.2f}  {f}:{n}  {txt[:90]}")
