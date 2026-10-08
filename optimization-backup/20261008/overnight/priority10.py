from pathlib import Path
import os,subprocess,json,time,re
r=Path(__file__).parent;old=Path('/puffertank/experiments/nethack-perf-20260917');d=r/'priority10';d.mkdir();rows=[]
e={k:v for k,v in os.environ.items() if not k.startswith(('NH_','NLE_','OMP_','GOMP_','PUF_','PUFFER_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','NETHACKOPTIONS')};e.update(NETHACKDIR=str(old/'dat'),NH_ZT_MASK='0',LD_LIBRARY_PATH=str(r/'pgo08/variant'),OMP_PROC_BIND='false')
for w in ['score','depth']:
 s=(old/'late512'/(w+'.c')).read_text()
 s=s.replace('static Session* replay_sessions;', '''static Session* replay_sessions;
#ifdef REPLAY_PRIORITY
static double *replay_cost;
typedef struct {double cost; int index;} CostIndex;
static int cost_order(const void* av,const void* bv) {const CostIndex *a=av,*b=bv; if(a->cost>b->cost)return -1;if(a->cost<b->cost)return 1;return a->index-b->index;}
#endif''')
 s=s.replace(' (void)unused;',''' (void)unused;
#ifdef REPLAY_PRIORITY
 double started=now();
#endif''',1)
 s=s.replace(' else step_session(&replay_sessions[i]);',''' else step_session(&replay_sessions[i]);
#ifdef REPLAY_PRIORITY
 replay_cost[i]=0.5*replay_cost[i]+0.5*(now()-started);
#endif''',1)
 needle=' for(int w=0;w<threads;w++)next[w*16]=lo+w*per;';repl='''
#ifdef REPLAY_PRIORITY
 assert(count%threads==0);
 CostIndex jobs[count],order[count];
 for(int j=0;j<count;j++)jobs[j]=(CostIndex){replay_cost[lo+j],lo+j};
 qsort(jobs,count,sizeof(CostIndex),cost_order);
 for(int w=0;w<threads;w++)for(int j=0;j<per;j++)order[w*per+j]=jobs[j*threads+w];
#endif
'''+needle;assert needle in s;s=s.replace(needle,repl,1)
 needle='if(i>=hi)break;replay_one(NULL,i);';repl='''if(i>=hi)break;
#ifdef REPLAY_PRIORITY
 replay_one(NULL,order[i-lo].index);
#else
 replay_one(NULL,i);
#endif
''';assert needle in s;s=s.replace(needle,repl,1)
 s=s.replace(' replay_sessions=ss;', '''
#ifdef REPLAY_PRIORITY
 replay_cost=calloc(n,sizeof(double));assert(replay_cost);
#endif
 replay_sessions=ss;''',1)
 src=d/(w+'.c');src.write_text(s)
 for mode in ['baseline','priority']:
  tree=old/'shared-pool'/w/'source';cmd=['cc','-O2','-g','-fopenmp','-pthread','-DREPLAY_WS=1']+(['-DREPLAY_PRIORITY=1'] if mode=='priority' else [])+['-I'+str(old/'shared-pool'),'-I'+str(tree/'src'),'-I'+str(tree/'ocean/nethack'),'-I'+str(old/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(src),'-L'+str(old/'lib'),'-Wl,-rpath,'+str(old/'lib'),'-lnethack','-lm','-ldl','-o',str(d/(w+'-'+mode))]
  with (d/('build-'+w+'-'+mode+'.log')).open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
for w in ['score','depth']:
 corpus=old/('score-record' if w=='score' else 'depth-record-v2');paths=sorted(map(str,corpus.glob('*.trace')))[:128]
 for mode,label,exe in [('verify','verify','priority'),('time','before','baseline'),('time','candidate','priority'),('time','after','baseline')]:
  cmd=['taskset','-c','0,2,4,6,8,10,12,14',str(d/(w+'-'+exe)),mode,'8','20000','5000',*paths];print('START',w,label,flush=True);start=time.time();p=subprocess.run(cmd,env=dict(e,NH_DISC_SWAP=str(int(w=='depth'))),capture_output=True,text=True);row=dict(label=w+'-'+label,command=cmd,rc=p.returncode,seconds=time.time()-start,stdout=p.stdout,stderr=p.stderr);rows.append(row);(d/'results.json').write_text(json.dumps(rows,indent=2));print('DONE',w,label,p.returncode,p.stdout[-500:],flush=True);assert p.returncode==0,p.stderr[-1000:]
summary={}
for w in ['score','depth']:
 vals={p:float(re.search(r'measured_seconds=([\d.]+)',next(x for x in rows if x['label']==w+'-'+p)['stdout'])[1]) for p in ['before','candidate','after']};summary[w]=dict(**vals,gain_percent=((vals['before']+vals['after'])/2/vals['candidate']-1)*100,drift_percent=(vals['after']/vals['before']-1)*100)
(d/'summary.json').write_text(json.dumps(summary,indent=2));print('PRIORITY_COMPLETE',summary,flush=True)
