from pathlib import Path
r=Path(__file__).parent;s=(r/'priority10.py').read_text().replace("d=r/'priority10'","d=r/'priority34'").replace("r/'pgo08/variant'","r/'pgo20/variant'")
needle=" src=d/(w+'.c');src.write_text(s)"
insert=''' s=s.replace('static double *replay_cost;', 'static double *replay_cost;\\nstatic int priority_round[4*16];')
 s=s.replace('typedef struct {double cost; int index;} CostIndex;', 'typedef struct {double cost; int index;} CostIndex;\\nstatic CostIndex *replay_order;')
 s=s.replace('double started=now();', 'int sampled=*(int*)unused; double started=sampled?now():0;')
 s=s.replace('replay_cost[i]=0.5*replay_cost[i]+0.5*(now()-started);', 'if(sampled)replay_cost[i]=0.5*replay_cost[i]+0.5*(now()-started);')
 s=s.replace('CostIndex jobs[count],order[count];', 'int sampled=!(priority_round[buffer*16]++ & 15);\\n CostIndex *order=replay_order+lo;\\n if(sampled) { CostIndex jobs[count];')
 s=s.replace('order[w*per+j]=jobs[j*threads+w];', 'order[w*per+j]=jobs[j*threads+w];\\n }')
 s=s.replace('replay_one(NULL,order[i-lo].index);','replay_one(&sampled,order[i-lo].index);')
 s=s.replace('replay_cost=calloc(n,sizeof(double));assert(replay_cost);','replay_cost=calloc(n,sizeof(double));assert(replay_cost);\\n replay_order=calloc(n,sizeof(CostIndex));assert(replay_order);')
'''
assert needle in s;s=s.replace(needle,insert+needle);(r/'priority34.py').write_text(s)
