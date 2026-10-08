#!/usr/bin/env python3
"""Summarise completed fixed-work ABA triplets; never treat partial pairs as wins."""
import argparse,json,re,statistics
from pathlib import Path
r=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('input',type=Path,nargs='?',default=r/'v3-validation-timings.json');p.add_argument('--output',type=Path);a=p.parse_args()
if not a.input.exists():raise SystemExit('No completed results yet')
rows=json.loads(a.input.read_text());groups={};checks=[]
for row in rows:
 label=row.get('label','');m=re.fullmatch(r'(.+)-vs-(.+)-r(\d+)-(before|candidate|after)',label)
 if not m:
  checks.append({k:row.get(k) for k in ['workload','variant','mode','rc']});continue
 old,new,rep,phase=m.groups();groups.setdefault((row['workload'],old,new,int(rep)),{})[phase]=row
summary={};incomplete=[]
for (work,old,new,rep),g in groups.items():
 if set(g)!={'before','candidate','after'}:incomplete.append((work,old,new,rep));continue
 data=[]
 for phase in ['before','candidate','after']:
  row=g[phase];assert row['rc']==0 and row['mode']=='time'
  result=re.search(r'^RESULT (.+)$',row['stdout'],re.M);assert result
  fields=dict(re.findall(r'(\w+)=([^ ]+)',result[1]));data.append(fields)
 for key in ['envs','threads','warmup','limit','measured_steps','measured_keys','positive_turn_advances']:
  assert len({x[key] for x in data})==1,(work,old,new,rep,'unequal work',key)
 t=[float(x['measured_seconds']) for x in data];assert min(t)>0
 item=dict(repeat=rep,throughput_ratio=(t[0]+t[2])/(2*t[1]),baseline_drift_percent=100*(t[2]/t[0]-1),measured_seconds=t,decisions=int(data[0]['measured_steps']),keys=int(data[0]['measured_keys']),maxrss_kb=[int(x['maxrss_kb']) for x in data])
 summary.setdefault(f'{work}:{old}->{new}',[]).append(item)
report={'input':str(a.input),'verification':checks,'incomplete_triplets':incomplete,'comparisons':{}}
for label,items in summary.items():
 ratios=[x['throughput_ratio'] for x in items]
 v=dict(completed_triplets=len(items),median_throughput_change_percent=100*(statistics.median(ratios)-1),min_ratio=min(ratios),max_ratio=max(ratios),baseline_drift_over_5_percent=any(abs(x['baseline_drift_percent'])>5 for x in items),triplets=items)
 report['comparisons'][label]=v
 print(label,':',len(items),'triplets; median throughput change',round(v['median_throughput_change_percent'],2),'%; drift flag',v['baseline_drift_over_5_percent'])
if incomplete:print('Incomplete triplets:',incomplete)
if a.output:a.output.write_text(json.dumps(report,indent=2))
