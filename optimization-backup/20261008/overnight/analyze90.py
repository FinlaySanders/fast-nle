from pathlib import Path
import sqlite3,json
r=Path(__file__).parent;d=r/'profile90-rollout';db=sqlite3.connect(d/'rollout.sqlite')
def union(xs):
 out=[]
 for a,b in sorted(xs):
  a=max(0,a);b=min(8000000000,b)
  if b<=a:continue
  if out and a<=out[-1][1]:out[-1]=(out[-1][0],max(out[-1][1],b))
  else:out.append((a,b))
 return out
def length(xs):return sum(b-a for a,b in union(xs))*1e-9
graphs=db.execute('select start,end from CUPTI_ACTIVITY_KIND_GRAPH_TRACE').fetchall();copies=db.execute('select start,end from CUPTI_ACTIVITY_KIND_MEMCPY').fetchall();gpu=union(graphs+copies)
threads=[]
for tid,n,t in db.execute('select globalTid,count(*),sum(end-start)*1e-9 from CUPTI_ACTIVITY_KIND_RUNTIME group by globalTid order by count(*) desc limit 4'):
 apis=[dict(name=name,count=c,seconds=ns*1e-9) for name,c,ns in db.execute('select s.value,count(*),sum(o.end-o.start) from CUPTI_ACTIVITY_KIND_RUNTIME o join StringIds s on s.id=o.nameId where globalTid=? group by nameId order by sum(o.end-o.start) desc',(tid,))]
 cond=db.execute("select o.start,o.end from OSRT_API o join StringIds s on s.id=o.nameId where globalTid=? and s.value='pthread_cond_wait'",(tid,)).fetchall()
 threads.append(dict(globalTid=tid,linux_tid=tid&0xffffff,cuda_calls=n,cuda_api_seconds=t,condition_wait_seconds=length(cond),api_breakdown=apis))
result=dict(capture_seconds=8,gpu_graph_envelope_union_seconds=length(graphs),gpu_graph_and_copy_envelope_union_seconds=length(gpu),gpu_graph_and_copy_envelope_fraction=length(gpu)/8,coordinator_threads=threads,notes=['Four GPU coordinator threads: summing their API waits does not give wall-clock stall time.','Graph spans are envelopes, may include internal gaps; this is not a kernel-utilization percentage.','OSRT capture excludes calls shorter than10us and concurrent worker waits overlap.','Capture delayed25s to mature policy rollouts; all32block observations and initial RNG/loadedweights match baseline.','Traced durations are diagnostic, not performance claims.'])
(d/'analysis.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
