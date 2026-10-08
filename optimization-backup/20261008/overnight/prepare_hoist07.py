from pathlib import Path
import subprocess
r=Path(__file__).parent;p=r/'engine-source/src/mon.c';b=r/'hoist07-before.c';assert not b.exists();b.write_bytes(p.read_bytes());s=p.read_text();a=s.index('int mfndpos(');z=s.index('\n}',a);part=s[a:z]
part=part.replace('boolean poisongas_ok, in_poisongas;', 'boolean poisongas_ok, in_poisongas;\n    boolean monseeu = (mon->mcansee && (!Invis || perceives(mdat)));')
needle='''                boolean monseeu =
                    (mon->mcansee && (!Invis || perceives(mdat)));
''';assert needle in part;part=part.replace(needle,'');s=s[:a]+part+s[z:];p.write_text(s);(r/'hoist07.patch').write_bytes(subprocess.run(['diff','-u',str(b),str(p)],capture_output=True).stdout)
