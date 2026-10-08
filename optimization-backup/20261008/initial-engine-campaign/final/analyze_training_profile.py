from pathlib import Path
import sqlite3,json,bisect,collections
root=Path(__file__).resolve().parent/'training-profile';results=[]
for label in ['original','optimized-retry']:
 db=sqlite3.connect(root/label/'timeline.sqlite');strings=dict(db.execute('select id,value from StringIds'));ranges=collections.defaultdict(list)
 for s,e,tid,txt in db.execute('select start,end,globalTid,text from NVTX_EVENTS where end is not null order by start'):
  ranges[tid].append((s,e,txt))
 starts={tid:[v[0] for v in rs] for tid,rs in ranges.items()};classify={}
 for s,e,tid,corr in db.execute('select start,end,globalTid,correlationId from CUPTI_ACTIVITY_KIND_RUNTIME'):
  rs=ranges[tid];i=bisect.bisect_right(starts.get(tid,[]),s)-1
  classify[corr]=rs[i][2] if i>=0 and rs[i][0]<=s<=rs[i][1] else 'unattributed'
 # Clip to the requested 15-second capture; calculate unions, never sum concurrent kernels as wall time.
 upper=15_000_000_000;unions=collections.defaultdict(list);sums=collections.Counter();counts=collections.Counter();names=collections.Counter()
 def add(k,s,e):
  s=max(0,s);e=min(upper,e)
  if e<=s:return
  a=unions[k]
  if a and s<=a[-1][1]:a[-1][1]=max(e,a[-1][1])
  else:a.append([s,e])
 for s,e,corr,name in db.execute('select start,end,correlationId,demangledName from CUPTI_ACTIVITY_KIND_KERNEL order by start'):
  tag=classify.get(corr,'unattributed');add(tag,s,e);add('all_kernels',s,e);dt=max(0,min(e,upper)-max(s,0));sums[tag]+=dt;counts[tag]+=1;names[strings[name]]+=dt
 dur={k:sum(e-s for s,e in a)/1e9 for k,a in unions.items()}
 # Host enqueue ranges are not GPU execution durations; GPU categories are assigned by CUDA correlation IDs.
 both=[]
 for k in ['fused_rollout','train_forward_backward']:both+=unions[k]
 both.sort();tmp=[]
 for s,e in both:
  if tmp and s<=tmp[-1][1]:tmp[-1][1]=max(e,tmp[-1][1])
  else:tmp.append([s,e])
 combined=sum(e-s for s,e in tmp)/1e9;overlap=dur.get('fused_rollout',0)+dur.get('train_forward_backward',0)-combined
 rows=dict(label=label,capture_seconds=15,kernel_busy_seconds=dur['all_kernels'],kernel_busy_percent=dur['all_kernels']/15*100,gpu_union_seconds=dur,overlapping_training_and_inference_seconds=overlap,kernel_duration_sum_seconds={k:v/1e9 for k,v in sums.items()},kernel_count=dict(counts),top_kernels=[dict(name=n,seconds=v/1e9,fraction_of_summed_kernel_time=v/sum(names.values())) for n,v in names.most_common(10)],scope='15-second warmed Nsight trace. CUDA correlation IDs associate kernels with existing NVTX inference/PPO enqueue ranges. GPU busy is union of kernel intervals, not occupancy or utilization of all SMs. Concurrent kernel-duration sums exceed wall time; profiles have overhead and are not clean throughput measurements.')
 results.append(rows)
(root/'summary.json').write_text(json.dumps(results,indent=2));print(json.dumps(results,indent=2))
