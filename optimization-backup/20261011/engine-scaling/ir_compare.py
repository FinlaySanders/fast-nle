# Per-function instruction counts per policy step for two callgrind dumps: ir_compare.py <labelA> <labelB> [topN]
import subprocess,sys,re,collections
from pathlib import Path
R=Path(__file__).resolve().parent; STEPS=512*128
def load(label):
    out=subprocess.run(['callgrind_annotate','--inclusive=no','--threshold=100','--show=Ir','--show-percs=no','--auto=no',str(R/('callgrind.'+label+'.out.1'))],capture_output=True,text=True).stdout
    tot=None; fn=collections.Counter()
    for ln in out.splitlines():
        t=ln.split()
        if len(t)>=2 and t[0].replace(',','').isdigit():
            v=int(t[0].replace(',',''))
            if 'PROGRAM TOTALS' in ln: tot=v; continue
            name=' '.join(t[1:]).split(':',1)[-1].split(' [')[0]
            base=re.sub(r"(\.lto_priv\.\d+|\.part\.\d+|\.constprop\.\d+|\.isra\.\d+|'\d+)","",name)
            fn[base]+=v
    return tot,fn
a,b=sys.argv[1],sys.argv[2]; top=int(sys.argv[3]) if len(sys.argv)>3 else 30
ta,fa=load(a); tb,fb=load(b)
print(f'instructions/step: {a} {ta/STEPS/1000:.1f}K  {b} {tb/STEPS/1000:.1f}K  ({(tb-ta)/ta*100:+.2f}%)\n')
print(f"{'function':44}{a:>10}{b:>10}{'delta':>9}")
rows=sorted(set(fa)|set(fb),key=lambda k:-(abs(fa[k]-fb[k])))
for k in rows[:top]:
    print(f"{k[:44]:44}{fa[k]/STEPS/1000:>9.1f}K{fb[k]/STEPS/1000:>9.1f}K{(fb[k]-fa[k])/STEPS/1000:>+8.1f}K")
