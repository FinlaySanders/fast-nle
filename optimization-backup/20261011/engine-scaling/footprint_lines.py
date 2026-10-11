# Per-source-line LL read misses at the 2048-game share (debug-info twin of the retained engine).
import re,subprocess,collections,sys
from pathlib import Path
R=Path(__file__).resolve().parent; STEPS=512*128
LABEL=sys.argv[1] if len(sys.argv)>1 else 'lines2048'; ENGINE=sys.argv[2] if len(sys.argv)>2 else 'footprint_g'
SRC=R.parent/('nethack-compact-state-20261008/engines/'+ENGINE+'/source')
out=subprocess.run(['callgrind_annotate','--inclusive=no','--threshold=100','--show-percs=no','--auto=yes',str(R/('callgrind.'+LABEL+'.out.1'))],capture_output=True,text=True).stdout
events=None; cur=None; lines=[]; edges=[]; fn=collections.Counter()
for ln in out.splitlines():
    m=re.search(r'Events\s+shown:\s+(.*)',ln)
    if m: events=m.group(1).split(); continue
    m=re.match(r'^-- Auto-annotated source: (.*)$',ln)
    if m: cur=m.group(1).strip(); src=Path(cur); srclines=src.read_text(errors='replace').splitlines() if src.exists() else []; lineno=0; continue
    if cur and events:
        tok=ln.split()
        if len(tok)>len(events) and all(t=='.' or (t.replace(',','').isdigit() and any(c.isdigit() for c in t)) for t in tok[:len(events)]):
            nums=[0 if t=='.' else int(t.replace(',','')) for t in tok[:len(events)]]
            ev=dict(zip(events,nums))
            txt=' '.join(tok[len(events):])
            if txt.startswith('=>'):
                # call edge: inclusive cost of the callee called from the previous source line
                if ev.get('DLmr',0)>0: edges.append((ev['DLmr'],ev.get('D1mr',0),cur,lineno,txt[2:].strip()))
                continue
            lineno+=1
            if ev.get('DLmr',0)>0 and 'events annotated' not in txt: lines.append((ev['DLmr'],ev.get('D1mr',0),ev.get('Dr',0),cur,lineno,txt))
        elif ln.startswith('-- line '):
            mm=re.match(r'^-- line (\d+)',ln)
            if mm: lineno=int(mm.group(1))-1
        elif ln.strip() and not ln.startswith('--'): lineno+=1
print('# Line-level LL read misses per policy step, 2048-game share (retained source, -g twin)\n')
print('Only lines with DLmr>0 are listed; line numbers count annotated source rows (call-edge rows excluded), so they match the file.\n')
import collections as _c
byfile=_c.Counter(); 
for d,d1,dr,f,n,txt in lines: byfile[Path(f).name]+=d
tot=sum(byfile.values()); print(f'self-cost LL read misses accounted: {tot/STEPS:.1f} lines/step\n')
print(f"{'file':20}{'DLmr/step':>10}{'share':>7}")
for f,d in byfile.most_common(18): print(f"{f:20}{d/STEPS:>10.1f}{d/tot*100:>6.1f}%")
print()
print(f"{'DLmr/step':>10}{'D1mr/step':>10}  file:line  source")
for d,d1,dr,f,n,txt in sorted(lines,reverse=True)[:80]:
    print(f"{d/STEPS:>10.2f}{d1/STEPS:>10.1f}  {Path(f).name}:{n}  {txt[:90]}")

print()
print('libc call edges by inclusive LL read misses (callee cost attributed to the calling source line):')
print(f"{'DLmr/step':>10}{'D1mr/step':>10}  caller file:line  => callee")
import re as _re
sel=[e for e in edges if _re.search(r'sysdeps|malloc\.c|/string/|libc',e[4])]
for d,d1,f,n,callee in sorted(sel,reverse=True)[:40]:
    print(f"{d/STEPS:>10.2f}{d1/STEPS:>10.1f}  {Path(f).name}:{n}  => {callee[:100]}")

print()
print('Owners of cost attributed to inlined header lines (file:function rows with DLmr/step >= 0.5):')
plain=subprocess.run(['callgrind_annotate','--inclusive=no','--threshold=100','--show-percs=no','--auto=no',str(R/('callgrind.'+LABEL+'.out.1'))],capture_output=True,text=True).stdout
evs=None
for ln in plain.splitlines():
    m=re.search(r'Events\s+shown:\s+(.*)',ln)
    if m: evs=m.group(1).split(); continue
    if not evs: continue
    tok=ln.split()
    if len(tok)>len(evs) and all(t=='.' or t.replace(',','').isdigit() for t in tok[:len(evs)]):
        nums=[0 if t=='.' else int(t.replace(',','')) for t in tok[:len(evs)]]; ev=dict(zip(evs,nums)); name=' '.join(tok[len(evs):])
        if ev.get('DLmr',0)/STEPS>=0.5 and re.search(r'\.h:|\.hpp:|\.S:|\.tcc:',name): print(f"{ev['DLmr']/STEPS:>10.2f}{ev.get('D1mr',0)/STEPS:>10.1f}  {name[:120]}")
