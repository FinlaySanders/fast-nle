# Aggregate callgrind cache events per function into engine subsystems; bytes per policy step.
import re,subprocess,collections
from pathlib import Path
R=Path(__file__).resolve().parent
STEPS=512*128
CATS=[('monster movement',r'(m_move|dochug|movemon|mfndpos|monmove|dog_move|set_apparxy|m_cansee|mnearto|mon_track|disturb|onscary|undesirable|goodpos|mon_allowflags|m_digweapon)'),
 ('other monster',r'(mcalc|mon_regen|m_detach|makemon|mondata|likes_|resists_|mhitu|mattacku|mhitm|mattackm|dmgval|hmon|monnear|m_respond|newcham|mon_adjust|monster_nearby|mondied|m_initweap|dist2)'),
 ('player movement',r'(domove|test_move|spoteffects|lookaround|u_on_|teleds|pickup|check_special_room|movobj|nomul|u_wipe|invocation_pos|flush_screen)'),
 ('vision',r'(vision|clear_path|couldsee|cansee|does_block|view_from|right_side|left_side|_q[1-4]_path|block_point|unblock_point)'),
 ('display',r'(newsym|show_glyph|display_|docrt|map_background|map_object|map_trap|map_invisible|glyph_at|see_monsters|see_objects|see_traps|tmp_at|back_to_glyph|magic_map|feel_location|print_glyph|row_refresh)'),
 ('obs export / tty',r'(nle_|fill_obs|pack_obs|update_blstats|NetHackRL|rl_|tty_|cl_end|cl_eos|putstr|curs|xputc|xputs|term_|home|docorner|bot\b|botl|status|window|win_|glyph_export|export_)'),
 ('inventory weight',r'(weight|inv_weight|near_capacity|calc_capacity|max_capacity|inv_cnt|carrying|invent|encumber)'),
 ('floor objects',r'(fobj|sobj_at|object_at|floor_index|place_object|remove_object|obj_here|nxtobj|level\.objects|objects_at|pile)'),
 ('traps/engravings',r'(t_at|engr_at|sengr_at|trap)'),
 ('rng',r'(rn2|rnd|rne|rnl|rn1|rnz|RND|isaac|random|whichrng)'),
 ('alloc/libc',r'(malloc|free|calloc|realloc|memcpy|memset|memmove|strlen|strcpy|strcmp|sprintf|vsnprintf|_int_|mem_)'),
 ('harness',r'(step_one|step_at|rounds|puf_step|ep_|pool_|omp|gomp|GOMP|main)')]
def parse(path):
    txt=subprocess.run(['callgrind_annotate','--inclusive=no','--threshold=100','--show-percs=no','--auto=no',str(path)],capture_output=True,text=True).stdout
    events=None; rows={}
    for ln in txt.splitlines():
        if ln.startswith('Events'):
            m=re.search(r'Events\s+shown:\s+(.*)',ln) or re.search(r'Events\s+recorded:\s+(.*)',ln)
            if m: events=m.group(1).split()
            continue
        m=re.match(r'^\s*((?:(?:[\d,]+|\.)\s+)+)(\S.*)$',ln)
        if not m or events is None: continue
        nums=[0 if x=='.' else int(x.replace(',','')) for x in m.group(1).split()]
        if len(nums)!=len(events): continue
        name=m.group(2).strip()
        if 'PROGRAM TOTALS' in name: continue
        rows[name]=dict(zip(events,nums))
    return events,rows
def short(name):
    n=re.sub(r'\s*\[[^\]]*\]\s*$','',name.strip()); n=n.split(':')[-1]; return n
def classify(name):
    fn=short(name)
    for cat,pat in CATS:
        if re.search(pat,fn): return cat
    return 'other'
out=[]
res={}
for arm in ('share512','share2048'):
    p=R/f'callgrind.{arm}.out.1'
    if not p.exists(): p=R/f'callgrind.{arm}.out'
    if not p.exists() or p.stat().st_size<10000: out.append(f'missing or empty {p}'); continue
    events,rows=parse(p); res[arm]=(events,rows)
    tot=collections.Counter(); per=collections.defaultdict(collections.Counter)
    for name,ev in rows.items():
        c=classify(name)
        for k,v in ev.items(): tot[k]+=v; per[c][k]+=v
    out.append(f"\n## {arm}: {len(rows)} functions; per policy step: Dr {tot['Dr']/STEPS:,.0f} refs, D1mr {tot['D1mr']/STEPS:,.0f}, DLmr {tot['DLmr']/STEPS:,.0f} lines ({tot['DLmr']*64/STEPS/1024:,.1f} KB), DLmw {tot.get('DLmw',0)/STEPS:,.0f}")
    out.append(f"{'subsystem':22}{'Dr/step':>10}{'D1mr/step':>11}{'DLmr/step':>11}{'LL KB/step':>11}{'share':>7}")
    for c,ev in sorted(per.items(),key=lambda kv:-kv[1]['DLmr']):
        out.append(f"{c:22}{ev['Dr']/STEPS:>10,.0f}{ev['D1mr']/STEPS:>11,.1f}{ev['DLmr']/STEPS:>11,.1f}{ev['DLmr']*64/STEPS/1024:>11.2f}{ev['DLmr']/max(tot['DLmr'],1)*100:>6.1f}%")
    top=sorted(rows.items(),key=lambda kv:-kv[1].get('DLmr',0))[:25]
    out.append('\ntop functions by D1 read misses per step (lines touched beyond L1):')
    for name,ev in sorted(rows.items(),key=lambda kv:-kv[1].get('D1mr',0))[:20]: out.append(f"  {ev['D1mr']/STEPS:>8.1f}  {classify(name):18} {short(name)[:60]}")
    out.append('\ntop functions by LL read misses per step:')
    for name,ev in top: out.append(f"  {ev['DLmr']/STEPS:>8.1f}  {classify(name):18} {short(name)[:60]}")
if len(res)==2:
    e,a=res['share512']; _,b=res['share2048']
    out.append('\n## extra LL read misses at the 2048-game share vs the 512-game share, by function (top 25)')
    diff=sorted(((b.get(n,{}).get('DLmr',0)-a.get(n,{}).get('DLmr',0),n) for n in set(a)|set(b)),reverse=True)[:25]
    for d,n in diff: out.append(f"  {d/STEPS:>8.1f}  {classify(n):18} {short(n)[:70]}")
print('# Engine cache footprint (callgrind, retained engine, 512 games, warm 4096, measured 128 steps/game)')
print('\n'.join(out))
