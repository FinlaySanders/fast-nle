"""Verify this backup's content hashes and saved patch reconstruction."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def apply(path, cwd, reverse=False):
    command = ['git', 'apply'] + (['--reverse'] if reverse else []) + [str(path)]
    subprocess.run(command, cwd=cwd, check=True)


files = json.loads((HERE / 'MANIFEST.json').read_text())['files']
for rel, expected in files.items():
    path = REPO / rel
    assert path.stat().st_size == expected['bytes'], rel
    assert digest(path) == expected['sha256'], rel

with tempfile.TemporaryDirectory(prefix='nethack-backup-check-') as name:
    temp = Path(name)
    if (HERE / 'training').is_dir():
        shutil.copytree(HERE / 'training/baseline', temp / 'training')
        apply(HERE / 'training/optimizations-only.patch', temp / 'training')
        for rel in ['src/algo.cu', 'src/pufferl.cu', 'ocean/nethack/nethack.cu']:
            assert digest(temp / 'training' / rel) == digest(HERE / 'training/minimal' / rel), rel
        shutil.copytree(HERE / 'scheduler/retained', temp / 'scheduler')
        patch = HERE / 'scheduler/shared-pool83.patch'
        proof = json.loads((HERE / 'scheduler/pool83-review/manifest.json').read_text())
        apply(patch, temp / 'scheduler', reverse=True)
        assert digest(temp / 'scheduler/src/pufferl.cu') == proof['base_sha256']
        apply(patch, temp / 'scheduler')
        assert digest(temp / 'scheduler/src/pufferl.cu') == proof['result_sha256']
        assert digest(temp / 'scheduler/src/env_pool.h') == proof['header_sha256']
    else:
        expected = json.loads((HERE / 'overnight/pgo61-source-manifest.json').read_text())
        for rel, sha in expected.items():
            assert digest(REPO / rel) == sha, rel
            dst = temp / 'engine' / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO / rel, dst)
        patch = HERE / 'overnight/retained-through-gold60.patch'
        apply(patch, temp / 'engine', reverse=True)
        baseline = json.loads((HERE / 'overnight/engine-source-baseline-hashes.json').read_text())
        for rel, sha in baseline.items():
            assert digest(temp / 'engine' / rel) == sha, rel
        apply(patch, temp / 'engine')
        for rel, sha in expected.items():
            assert digest(temp / 'engine' / rel) == sha, rel

print(f'PASS: {len(files)} file hashes and saved patch reconstruction')
