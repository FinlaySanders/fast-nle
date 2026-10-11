# Compare LL/D1 misses per step between two callgrind arms: footprint_compare.py <labelA> <labelB>
import sys,subprocess,re,collections
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import footprint_report as fr
R=Path(__file__).resolve().parent; STEPS=512*128
def load(label):
    p=R/f'callgrind.{label}.out.1'
    if not p.exists(): p=R/f'callgrind.{label}.out'
    return fr.parse(p)[1]
a=load(sys.argv[1]); b=load(sys.argv[2])
def agg(rows):
    tot=collections.Counter(); per=collections.defaultdict(collections.Counter)
    for n,ev in rows.items():
        c=fr.classify(n)
        for k,v in ev.items(): tot[k]+=v; per[c][k]+=v
    return tot,per
ta,pa=agg(a); tb,pb=agg(b)
print(f"{'':22}{sys.argv[1]:>22}{sys.argv[2]:>22}")
for k in ('Dr','D1mr','DLmr','DLmw'): print(f"{k+'/step':22}{ta[k]/STEPS:>22,.1f}{tb[k]/STEPS:>22,.1f}  ({(tb[k]/max(ta[k],1)-1)*100:+.1f}%)")
print(f"\n{'subsystem':22}{'DLmr A':>10}{'DLmr B':>10}{'delta':>8}   {'D1mr A':>10}{'D1mr B':>10}")
for c in sorted(set(pa)|set(pb),key=lambda c:-pa[c]['DLmr']):
    print(f"{c:22}{pa[c]['DLmr']/STEPS:>10.1f}{pb[c]['DLmr']/STEPS:>10.1f}{(pb[c]['DLmr']-pa[c]['DLmr'])/STEPS:>+8.1f}   {pa[c]['D1mr']/STEPS:>10.1f}{pb[c]['D1mr']/STEPS:>10.1f}")
