from pathlib import Path
import shutil,subprocess
r=Path(__file__).resolve().parent
for work in ('depth','score'):
 old=r if work=='depth' else r/'score';new=r/'harness-v3'/work
 (new/'source/ocean').mkdir(parents=True,exist_ok=True)
 shutil.copytree(old/'source/ocean/nethack',new/'source/ocean/nethack',dirs_exist_ok=True)
 (new/'source/src').symlink_to(old/'source/src',target_is_directory=True)
 p=new/'source/ocean/nethack/nethack.h';t=p.read_text().replace('    FILE* trace_file;','    FILE* trace_file;\n    FILE* trace_aug_file;\n    int trace_version;');p.write_text(t)
 p=new/'source/ocean/nethack/perf_trace.h';t=p.read_text()
 t=t.replace('    e->trace_events++;','''    if(e->trace_aug_file) {
        assert(fwrite(&kind,1,1,e->trace_aug_file)==1);
        assert(fwrite(data,1,n,e->trace_aug_file)==n);
    }
    e->trace_events++;''')
 t=t.replace('memcpy(h.magic,"NHPERF1",7);','memcpy(h.magic,"NHPERF2",7);e->trace_version=2;')
 t=t.replace('static void trace_engine(Nethack* e,char kind) {\n    if(!e->trace_file)return;','static uint64_t trace_engine_hash(Nethack* e) {')
 t=t.replace("    trace_io(e,kind,&h,sizeof(h));\n}",'''    return h;
}
static void trace_engine(Nethack* e,char kind) {
    if(!e->trace_file)return;
    uint64_t h=trace_engine_hash(e);trace_io(e,kind,&h,sizeof(h));
}
static void trace_extra_refresh(Nethack* e) {
    if(e->trace_version==2) {trace_engine(e,'F');return;}
    if(e->trace_aug_file) {
        uint64_t h=trace_engine_hash(e);char kind='F';
        assert(fwrite(&kind,1,1,e->trace_aug_file)==1);
        assert(fwrite(&h,1,sizeof(h),e->trace_aug_file)==sizeof(h));
    }
}''',1)
 p.write_text(t)
 p=new/'source/ocean/nethack/macros.h';t=p.read_text();needle='    if (!env->obs.done) nle_obs_refresh(env->ctx, &env->obs);';assert t.count(needle)==1
 t=t.replace(needle,"    if (!env->obs.done) { nle_obs_refresh(env->ctx, &env->obs); trace_extra_refresh(env); }");p.write_text(t)
 t=(old/'replay_vec_v2.c').read_text().replace('load_session(const char* path,int verify)','load_session(const char* path,int verify,int engine)')
 t=t.replace('assert(!memcmp(h.magic,"NHPERF1",7));','assert(!memcmp(h.magic,"NHPERF1",7) || !memcmp(h.magic,"NHPERF2",7));\n if(engine && h.magic[6]!=\'2\') {fprintf(stderr,"Engine-only replay requires complete NHPERF2 traces; augment via full verification first.\\n");exit(2);}')
 t=t.replace('s.e=e;e->rng=h.rng;','s.e=e;e->rng=h.rng;e->trace_version=h.magic[6]-\'0\';')
 needle='nethack_sync_buffers(e);nethack_do_reset(e);return s;'
 t=t.replace(needle,'''const char *aug=getenv("NH_PERF_AUGMENT");
 if(aug) {
  assert(verify && !engine);char name[4096];snprintf(name,sizeof(name),"%s/env%05u.trace",aug,h.rng);
  e->trace_aug_file=fopen(name,"wbx");assert(e->trace_aug_file);
  setvbuf(e->trace_aug_file,NULL,_IOFBF,65536);memcpy(h.magic,"NHPERF2",7);
  assert(fwrite(&h,1,sizeof(h),e->trace_aug_file)==sizeof(h));
 }
 nethack_sync_buffers(e);nethack_do_reset(e);return s;''')
 t=t.replace('load_session(argv[5],verify)','load_session(argv[5],verify,engine)').replace('load_session(argv[5+i],verify)','load_session(argv[5+i],verify,engine)')
 t=t.replace('Nethack* e=s->e;puf_close(e);','Nethack* e=s->e;if(e->trace_aug_file){assert(fclose(e->trace_aug_file)==0);e->trace_aug_file=NULL;}puf_close(e);')
 (new/'replay_vec.c').write_text(t)
 cmd=['cc','-O2','-g','-fopenmp','-I'+str(new/'source/src'),'-I'+str(new/'source/ocean/nethack'),'-I'+str(r/'engine-baseline/include'),'-I/puffertank/pufferlib/vendor/fast-nle/build/_deps/deboost_context-src/include','-I/puffertank/pufferlib/raylib-5.5_linux_amd64/include',str(new/'replay_vec.c'),'-L'+str(r/'lib'),'-Wl,-rpath,'+str(r/'lib'),'-lnethack','-lm','-ldl','-o',str(new/'replay_vec')]
 p=subprocess.run(cmd,capture_output=True,text=True);(new/'build.log').write_text(p.stdout+p.stderr);print(work,p.returncode,flush=True)
 if p.returncode:raise RuntimeError(p.stderr)
