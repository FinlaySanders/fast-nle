from pathlib import Path
import json,sys,datetime
r=Path(__file__).parent;candidate=sys.argv[1];d=r/(candidate+'-training');a={p.parent.name:json.loads(p.read_text()) for p in d.glob('*/result.json')};assert set(a)=={'baseline-before',candidate,'baseline-after'}
before=a['baseline-before']['seconds'];after=a['baseline-after']['seconds'];v=a[candidate]['seconds'];result=dict(time=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=candidate+'-training',seconds={k:x['seconds'] for k,x in a.items()},mean_turns={k:x['mean_turn'] for k,x in a.items()},gain_percent=((before+after)/2/v-1)*100,drift_percent=(after/before-1)*100,measured_steps=a[candidate]['steps'],caveat='Loaded mature checkpoint with fresh optimizer; async training trajectories/game ages differ between arms. This is a whole-training observation, not exact fixed-trajectory timing or an additional gain on top of earlier combined results.')
(d/'summary.json').write_text(json.dumps(result,indent=2))
with (r/'ledger.jsonl').open('a') as f:f.write(json.dumps(result)+'\n')
print(json.dumps(result,indent=2))
