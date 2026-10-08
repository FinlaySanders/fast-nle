from pathlib import Path
import sqlite3,json,collections
r=Path(__file__).parent;d=r/'profile113';db=sqlite3.connect(d/'rollout.sqlite');lo=250000000;hi=3750000000;dur=hi-lo
nv=db.execute('select n.start,n.end,n.globalTid,coalesce(n.text,s.value) from NVTX_EVENTS n left join StringIds s on s.id=n.textId where n.end is not null and n.end>? and n.start<?',(lo,hi)).fetchall()
coords=sorted({tid for a,b,tid,name in nv if name=='rollout.env'});assert len(coords)==4
names=['rollout.env','rollout.gpu_wait','rollout.gpu_submit','rollout.upload','pool.tail_wait','pool.reader_drain','pool.submitter_work','pool.worker_work'];events=[];sumtime=collections.Counter();bytid=collections.defaultdict(collections.Counter)
for a,b,tid,name in nv:
 if name not in names:continue
 a=max(lo,a);b=min(hi,b)
 sumtime[name]+=b-a;bytid[tid][name]+=b-a
 events.extend([(a,name,1),(b,name,-1)])
kt=db.execute('select start,end from CUPTI_ACTIVITY_KIND_GRAPH_TRACE where end>? and start<?',(lo,hi)).fetchall();kern=collections.Counter();counts=collections.Counter()
for a,b in kt:
 a=max(a,lo);b=min(b,hi);kern['CUDA graph envelope']+=b-a;counts['CUDA graph envelope']+=1
 events.extend([(a,'kernel',1),(b,'kernel',-1)])
for a,b in db.execute('select start,end from CUPTI_ACTIVITY_KIND_MEMCPY where end>? and start<?',(lo,hi)):
 events.extend([(max(a,lo),'copy',1),(min(b,hi),'copy',-1)])
active=collections.Counter();tot=collections.Counter();hist=collections.Counter();last=lo
for t,kind,delta in sorted(events):
 dt=t-last
 if dt:
  gpu=active['kernel']>0 or active['copy']>0
  tot['gpu_active' if gpu else 'gpu_idle']+=dt
  if active['kernel']:tot['kernel_active']+=dt
  if active['copy']:tot['copy_active']+=dt
  if active['rollout.env']:tot['any_env']+=dt
  if gpu and active['rollout.env']:tot['gpu_env_overlap']+=dt
  if not gpu:
   if active['rollout.env']==4:tot['idle_all4_env']+=dt
   elif active['rollout.env']:tot['idle_mixed_env']+=dt
   else:tot['idle_no_env']+=dt
   if active['pool.tail_wait']==4:tot['idle_all4_tail']+=dt
   if active['rollout.gpu_wait']:tot['idle_any_gpu_wait']+=dt
  hist[active['pool.worker_work']+active['pool.submitter_work']]+=dt
 active[kind]+=delta;assert active[kind]>=0,(kind,active[kind]);last=t
assert last==hi
result=dict(window_seconds=dur/1e9,window_start_seconds=lo/1e9,window_end_seconds=hi/1e9,wall_time_percent={k:100*v/dur for k,v in tot.items()},average_coordinator_percent={k:100*v/(4*dur) for k,v in sumtime.items() if k!='pool.worker_work'},mean_workers_in_claim=sumtime['pool.worker_work']/dur,work_claim_concurrency_seconds={str(k):v/1e9 for k,v in sorted(hist.items())},top_kernels=[dict(name=k,count=counts[k],summed_seconds=v/1e9,percent_of_summed_kernel_time=v/sum(kern.values())*100) for k,v in kern.most_common(12)],coordinators=[dict(tid=t&0xffffff,percent={k:v/dur*100 for k,v in bytid[t].items()}) for t in coords],notes=['Graph envelopes and copies only; envelope active includes internal gaps and is NOT kernel utilization.','CPU phases overlap across threads; average coordinator percentages are not serial wall-time decomposition.','worker_work includes task execution, atomic claiming and OS scheduling; not hardware CPU utilization.','Tail wait begins after submitter scans all queues; waits for already-claimed work to finish.','Four-second traced window trimmed250ms each end; trace overhead means these are diagnostic fractions, not uninstrumented speed claims.','All32observation checkpoints, initial RNG and loaded weights match retained pipeline.'])
(d/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k not in ['coordinators','work_claim_concurrency_seconds','notes']},indent=2))
