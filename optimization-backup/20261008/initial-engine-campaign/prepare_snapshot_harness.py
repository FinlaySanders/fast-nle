"""Prepare isolated optional raw-observation sidecars; build/validation is separate."""
from pathlib import Path
import shutil
r=Path(__file__).resolve().parent
for work in ('depth','score'):
 old=r/'harness-v3'/work; new=r/'harness-v4'/work
 assert not new.exists(),new
 shutil.copytree(old/'source/ocean',new/'source/ocean')
 (new/'source/src').symlink_to((old/'source/src').resolve(),target_is_directory=True)
 shutil.copy2(old/'replay_vec.c',new/'replay_vec.c')
 p=new/'source/ocean/nethack/nethack.h';t=p.read_text().replace('    FILE* trace_file;','    FILE* trace_file;\n    FILE* snapshot_file;\n    int snapshot_checked;')
 needle='    if (env->trace_file) { fclose(env->trace_file); env->trace_file=NULL; }'
 assert needle in t
 t=t.replace(needle,'    if (env->snapshot_file) { assert(fclose(env->snapshot_file)==0); env->snapshot_file=NULL; }\n'+needle);p.write_text(t)
 p=new/'source/ocean/nethack/perf_trace.h';t=p.read_text()
 helper='''
/* Sidecar records: event u64, kind u8, then (length u32, bytes) per field.
 * Native little-endian ABI, same as the frozen trace. NULL fields have length0.
 * Only enabled explicitly in recording/verification, never timing. */
static FILE* snapshot_begin(Nethack* e, char kind) {
    if(!e->snapshot_checked) {
        e->snapshot_checked=1;
        const char* dir=getenv("NH_PERF_SNAPSHOTS");
        if(dir) {
            assert(e->trace_mode!=3);
            char path[4096];snprintf(path,sizeof(path),"%s/env%05u.obs",dir,e->rng);
            e->snapshot_file=fopen(path,"wbx");assert(e->snapshot_file);
            assert(fwrite("NHOBS001",1,8,e->snapshot_file)==8);
            setvbuf(e->snapshot_file,NULL,_IOFBF,65536);
        }
    }
    FILE* f=e->snapshot_file;if(!f)return NULL;
    uint64_t event=e->trace_events;
    assert(fwrite(&event,8,1,f)==1);assert(fwrite(&kind,1,1,f)==1);return f;
}
static void snapshot_field(FILE* f,const void* data,size_t size) {
    if(!f)return;assert(size<=UINT32_MAX);uint32_t n=data?(uint32_t)size:0;
    assert(fwrite(&n,4,1,f)==1);if(n)assert(fwrite(data,1,n,f)==n);
}
'''
 t=t.replace('static uint64_t trace_engine_hash',helper+'\nstatic uint64_t trace_engine_hash',1)
 start=t.index('#define H(p,n)');end=t.index('#undef H',start)
 fields=t[start:end].split('\n',1)[1].replace('H(', 'snapshot_field(f,')
 needle='    uint64_t h=trace_engine_hash(e);trace_io(e,kind,&h,sizeof(h));'
 assert needle in t
 t=t.replace(needle,'    FILE* f=snapshot_begin(e,kind);\n'+fields+'\n'+needle)
 needle="    }trace_io(e,'O',&h,sizeof(h));"
 assert needle in t
 t=t.replace(needle,"""    }
    FILE* f=snapshot_begin(e,'O');
    snapshot_field(f,e->agents[0].observations,OBS_SIZE);
    int sizes2[]=ACT_SIZES;int n2=0;for(int i=0;i<NUM_ATNS;i++)n2+=sizes2[i];
    snapshot_field(f,e->agents[0].action_mask,n2);
    trace_io(e,'O',&h,sizeof(h));""")
 p.write_text(t)
print('Prepared v4 source only; NOT built or validated.')
