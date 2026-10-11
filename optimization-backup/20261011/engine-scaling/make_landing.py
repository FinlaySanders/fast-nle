# ablate_<tag>.json: trainer landing. ctrl = incpack_v39 + <ctrl_pgo_build>, cand = incpack_v39 + <cand_pgo_build>.
# Usage: make_landing.py <cand_pgo_build_dir> <tag> [ctrl_pgo_build_dir]
import json,sys,copy
from pathlib import Path
H=Path('/puffertank/experiments/nethack-24h-20261009'); cand=sys.argv[1]; tag=sys.argv[2]
ctrl=sys.argv[3] if len(sys.argv)>3 else '/puffertank/experiments/nethack-compact-state-20261008/engines/incstack2_pgo/build'
base=json.load(open(H/'ablate_landing2.json'))
tmpl={a['label'].split('_')[0]:a for a in base if a['label'].endswith('_landing')}
arms=[]
for reg,a in tmpl.items():
    r=reg.replace('abllanding2','')
    for suffix,lib in [('ctrl_a',ctrl),('cand_a',cand),('cand_b',cand),('ctrl_b',ctrl)]:
        b=copy.deepcopy(a); b['label']=f'{tag}{r}_{suffix}'; b['binary']='incpack_v39'; b['env']['LD_LIBRARY_PATH']=lib; arms.append(b)
json.dump(arms,open(H/f'ablate_{tag}.json','w'),indent=1); print(len(arms),'arms ->',H/f'ablate_{tag}.json'); print([a['label'] for a in arms])
