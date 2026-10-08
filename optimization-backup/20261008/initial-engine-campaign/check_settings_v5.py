"""Parse captured complete native settings; preserve literal paths, compare semantic fields separately."""
import ctypes as C,struct,json,argparse
from pathlib import Path
class Seeds(C.Structure):
 _fields_=[('seeds',C.c_ulong*2),('reseed',C.c_char),('use_init_seeds',C.c_bool),('lgen_seed',C.c_ulong),('use_lgen_seed',C.c_bool)]
class Settings(C.Structure):
 _fields_=[('hackdir',C.c_char*4096),('scoreprefix',C.c_char*4096),('options',C.c_char*32768),('wizkit',C.c_char*4096),('spawn_monsters',C.c_int),('underfoot_glyphs',C.c_int),('ttyrecname',C.c_char*4096),('initial_seeds',Seeds),('fix_moon_phase',C.c_bool),('time_seed',C.c_ulong),('time_seed_is_set',C.c_bool)]
def read(path):
 rows=[]
 with Path(path).open('rb') as f:
  assert f.read(8)==b'NHSET001';n=struct.unpack('<I',f.read(4))[0];assert n==C.sizeof(Settings),(n,C.sizeof(Settings))
  while b:=f.read(8):
   assert len(b)==8;event=struct.unpack('<Q',b)[0];payload=f.read(n);assert len(payload)==n
   s=Settings.from_buffer_copy(payload);rows.append(dict(event=event,paths={k:getattr(s,k).decode() for k in ['hackdir','scoreprefix','options','wizkit','ttyrecname']},semantic=dict(seeds=list(s.initial_seeds.seeds),reseed=s.initial_seeds.reseed.hex(),use_init_seeds=s.initial_seeds.use_init_seeds,lgen_seed=s.initial_seeds.lgen_seed,use_lgen_seed=s.initial_seeds.use_lgen_seed,spawn_monsters=s.spawn_monsters,underfoot_glyphs=s.underfoot_glyphs,fix_moon_phase=s.fix_moon_phase,time_seed=s.time_seed,time_seed_is_set=s.time_seed_is_set)))
 assert rows and rows[0]['event']==0 and all(a['event']<b['event'] for a,b in zip(rows,rows[1:]))
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('path',type=Path);a=p.parse_args();print(json.dumps(read(a.path),indent=2))
