from pathlib import Path
import shutil
r=Path(__file__).resolve().parent
for w in ['depth','score']:
 old=r/'harness-v4'/w/'source';dest=r/'harness-v5'/w/'source'
 def ignore(path,names):return [n for n in names if Path(path)==old and (n=='puffer' or n.startswith('puffer_') or n=='build')]
 shutil.copytree(old,dest,symlinks=True,ignore=ignore)
 p=dest/'ocean/nethack/perf_trace.h';s=p.read_text();assert 'NHOBS001' in s;s=s.replace('NHOBS001','NHOBS002')
 needle='    snapshot_field(f,e->obs.tty_chars,24*80);';assert s.count(needle)==1
 s=s.replace(needle,needle+'''
    snapshot_field(f,&e->obs.action,sizeof(e->obs.action));
    snapshot_field(f,&e->obs.in_normal_game,sizeof(e->obs.in_normal_game));
    snapshot_field(f,&e->obs.partial,sizeof(e->obs.partial));
    snapshot_field(f,e->obs.prog_state,NLE_PROGRAM_STATE_SIZE*sizeof(int));
    snapshot_field(f,e->obs.inv_strs,NLE_INVENTORY_SIZE*NLE_INVENTORY_STR_LENGTH);
    snapshot_field(f,e->obs.screen_descriptions,NH_GRID*NLE_SCREEN_DESCRIPTION_LENGTH);
    snapshot_field(f,e->obs.tty_colors,24*80);
    snapshot_field(f,e->obs.tty_cursor,2);''')
 needle="    trace_io(e,'R',&st,sizeof(st));";assert s.count(needle)==1
 s=s.replace(needle,'''    const char* snapshot_dir=getenv("NH_PERF_SNAPSHOTS");
    if(snapshot_dir) {
        char path[4096];snprintf(path,sizeof(path),"%s/env%05u.settings",snapshot_dir,e->rng);
        FILE* f=fopen(path,e->trace_events?"ab":"wbx");assert(f);
        if(!e->trace_events) { assert(fwrite("NHSET001",1,8,f)==8);uint32_t n=sizeof(e->settings);assert(fwrite(&n,4,1,f)==1); }
        uint64_t event=e->trace_events;assert(fwrite(&event,8,1,f)==1);
        assert(fwrite(&e->settings,1,sizeof(e->settings),f)==sizeof(e->settings));assert(fclose(f)==0);
    }
'''+needle)
 p.write_text(s);shutil.copy2(r/'harness-v4'/w/'replay_vec.c',r/'harness-v5'/w/'replay_vec.c')
# New checker retains v1 compatibility; engine legacy hash covers first15 fields,
# additional fields are checked by whole-file replay comparison.
s=(r/'check_snapshots.py').read_text();s=s.replace(" assert exact(s,8)==b'NHOBS001'"," magic=exact(s,8);assert magic in (b'NHOBS001',b'NHOBS002');engine_fields=24 if magic==b'NHOBS002' else 16")
s=s.replace("range(2 if kind=='O' else 16)","range(2 if kind=='O' else engine_fields)")
(r/'check_snapshots_v5.py').write_text(s)
print('Prepared version2 raw sidecar with all24 nle_obs fields; full settings sidecars added')
