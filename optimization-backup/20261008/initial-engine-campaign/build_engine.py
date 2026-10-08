from pathlib import Path
import subprocess
r=Path(__file__).parent
for name in ['engine-baseline','engine-candidate']:
 s=r/name;dep=Path('/puffertank/pufferlib/vendor/fast-nle/build/_deps')
 cmd=['cmake','-S',str(s),'-B',str(s/'build'),'-DCMAKE_BUILD_TYPE=RelWithDebInfo']
 for key,folder in [('PYBIND11','pybind11-src'),('DEBOOST_CONTEXT','deboost_context-src'),('BZIP2','bzip2-src')]:cmd.append('-DFETCHCONTENT_SOURCE_DIR_'+key+'='+str(dep/folder))
 with (r/(name+'-build.log')).open('w') as f:
  subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
  subprocess.run(['cmake','--build',str(s/'build'),'--target','nethack','-j','16'],stdout=f,stderr=subprocess.STDOUT,check=True)
 print('BUILT',name,flush=True)
(r/'ENGINES_BUILT').write_text('done\n')
