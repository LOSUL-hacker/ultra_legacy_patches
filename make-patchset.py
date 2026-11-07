#!/usr/bin/env python3
"""Export the net difference between each of your forks and its LineageOS upstream, one patch per project.

Usage: ./make-patchset.py [manifest-dir]   (default: reads fork list from ./forks.json)
Output: ./patches/<project path with / -> _ >.patch (net diff upstream->fork), ./patches/MANIFEST.tsv, ./patches/OWN-COMMITS.txt
"""
import json, subprocess, os, sys, shutil, concurrent.futures as cf

ENV = {'GIT_TERMINAL_PROMPT': '0', 'PATH': '/usr/bin:/bin:/usr/local/bin', 'HOME': os.environ.get('HOME', '/tmp')}
WORK = os.path.abspath('work'); OUT = os.path.abspath('patches')
DATES = ['2025-04-01', '2024-10-01', '2024-01-01', '2023-06-01', '2022-06-01', None]  # None = full history

def git(d, *a, check=False):
    r = subprocess.run(['git', '-C', d, *a], capture_output=True, text=True, env=ENV)
    if check and r.returncode: raise RuntimeError(r.stderr.strip())
    return r

def export(row):
    path, fork, upstream, branch = row['path'], row['fork'], row['upstream'], row['branch']
    safe = path.replace('/', '_'); d = f'{WORK}/{safe}'
    shutil.rmtree(d, ignore_errors=True); os.makedirs(d)
    git(d, 'init', '-q', '--bare')
    git(d, 'remote', 'add', 'up', f'https://github.com/{upstream}'); git(d, 'remote', 'add', 'fork', f'https://github.com/{fork}')
    base = None
    for date in DATES:
        extra = [f'--shallow-since={date}'] if date else []
        a = git(d, 'fetch', '-q', '--filter=blob:none', *extra, 'up', f'+{branch}:refs/heads/up')
        if a.returncode:
            if 'shallow info' in a.stderr: continue          # nothing newer than this date upstream: go deeper
            return dict(row, error=a.stderr[:200], n=0)
        b = git(d, 'fetch', '-q', '--filter=blob:none', *extra, 'fork', f'+{branch}:refs/heads/fork')
        if b.returncode:
            if 'shallow info' in b.stderr: continue
            return dict(row, error=b.stderr[:200], n=0)
        mb = git(d, 'merge-base', 'up', 'fork')
        if mb.returncode or not mb.stdout.strip(): continue
        cand = mb.stdout.strip()
        sh = open(f'{d}/shallow').read().split() if os.path.exists(f'{d}/shallow') else []
        if cand in sh and date: continue                      # boundary commit = artifact of the window, go deeper
        base = cand; break
    unrelated = base is None
    ref = 'up' if unrelated else base        # unrelated histories: diff against upstream tip (best available)
    diff = git(d, 'diff', '--binary', '--full-index', ref, 'fork')
    if diff.returncode: return dict(row, error=diff.stderr[:200], n=0)
    own = git(d, 'log', '--no-merges', '--format=%cs %an | %s', 'up..fork').stdout.strip().splitlines()
    stat = git(d, 'diff', '--shortstat', ref, 'fork').stdout.strip()
    if diff.stdout.strip():
        open(f'{OUT}/{safe}.patch', 'w').write(diff.stdout)
    behind = git(d, 'rev-list', '--count', 'fork..up').stdout.strip() if not unrelated else '?'
    return dict(row, base=(ref[:12] if not unrelated else 'UNRELATED-HISTORY'), n=1 if diff.stdout.strip() else 0,
                stat=stat or 'identical to upstream', own=own, behind=behind)

if __name__ == '__main__':
    rows = json.load(open('forks.json'))
    os.makedirs(OUT, exist_ok=True)
    with cf.ThreadPoolExecutor(5) as ex: res = list(ex.map(export, rows))
    with open(f'{OUT}/MANIFEST.tsv', 'w') as f:
        f.write('path\tfork\tupstream\tbranch\tbase\tpatch_file\n')
        for r in res:
            pf = r['path'].replace('/', '_') + '.patch' if r.get('n') else '-'
            f.write(f"{r['path']}\t{r['fork']}\t{r['upstream']}\t{r['branch']}\t{r.get('base','')}\t{pf}\n")
    with open(f'{OUT}/OWN-COMMITS.txt', 'w') as f:
        for r in res:
            f.write(f"## {r['path']}  ({r['fork']})  {r.get('stat','')}\n")
            for l in r.get('own', []): f.write(f"   {l}\n")
    for r in res:
        print(f"{r['path']:34s} {r.get('stat') or r.get('error'):58s} {'[behind upstream by '+str(r['behind'])+']' if r.get('behind') not in (None,'0') else ''}")
