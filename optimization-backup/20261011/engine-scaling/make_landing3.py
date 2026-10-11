# ablate_landing3.json: trainer landing of the new engine layers. ctrl = incpack_v39 + incstack2_pgo (current best stack),
# cand = incpack_v39 + <engine>_pgo. Usage: make_landing3.py <engine_pgo_build_dir>
import json,sys,copy
from pathlib import Path
H=Path('/puffertank/experiments/nethack-24h-20261009'); cand=sys.argv[1]
ctrl='/puffertank/experiments/nethack-compact-state-20261008/engines/incstack2_pgo/build'
base=json.load(open(H/'ablate_landing2.json'))
tmpl={a['label'].split('_')[0]:a for a in base if a['label'].endswith('_landing')}
arms=[]
for reg,a in tmpl.items():
    r=reg.replace('abllanding2','')
    for suffix,lib in [('ctrl_a',ctrl),('cand_a',cand),('cand_b',cand),('ctrl_b',ctrl)]:
        b=copy.deepcopy(a); b['label']=f'landing3{r}_{suffix}'; b['binary']='incpack_v39'; b['env']['LD_LIBRARY_PATH']=lib; arms.append(b)
json.dump(arms,open(H/'ablate_landing3.json','w'),indent=1); print(len(arms),'arms ->',H/'ablate_landing3.json'); print([a['label'] for a in arms])
