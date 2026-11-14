#!/usr/bin/env python3
"""Trigger eval: does Claude invoke this skill for the right requests (and only those)?

Runs each case in evals/triggers.json through the Claude Code CLI with this repository
loaded as a plugin, in an empty temporary folder, with file/shell tools denied, and
stops after the first turns. A case passes when the skill was (or was not) invoked as
expected. Each case is a real, billed model call: use --limit / --case while iterating.

    python scripts/eval_triggers.py                 # all cases
    python scripts/eval_triggers.py --case ar-gulf-dialect --case neg-email
    python scripts/eval_triggers.py --runs 3 --model sonnet --json evals/results.json
"""
import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DENY = 'Bash,Write,Edit,NotebookEdit,WebFetch,WebSearch,Task,Agent'


def run_error(stream_lines):
    """Return an error message when the run itself failed (auth, API, …), else ''."""
    for line in stream_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') == 'result' and event.get('is_error'):
            return str(event.get('result') or event.get('subtype') or 'error')[:200]
        if event.get('type') == 'assistant' and event.get('message', {}).get('model') == '<synthetic>':
            texts = [b.get('text', '') for b in event['message'].get('content', []) if b.get('type') == 'text']
            return (' '.join(texts) or 'synthetic error message')[:200]
    return ''


def invoked_skill(stream_lines, skill):
    for line in stream_lines:
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get('type') != 'assistant':
            continue
        for block in event.get('message', {}).get('content', []):
            if block.get('type') == 'tool_use' and block.get('name') == 'Skill':
                name = str(block.get('input', {}).get('skill', ''))
                if name == skill or name.endswith(':' + skill) or name.startswith(skill + ':'):
                    return True
    return False


def run_case(case, skill, model, timeout):
    with tempfile.TemporaryDirectory() as cwd:
        cmd = ['claude', '-p', case['prompt'], '--plugin-dir', str(ROOT), '--output-format', 'stream-json',
               '--verbose', '--max-turns', '2', '--disallowedTools', DENY]
        if model:
            cmd += ['--model', model]
        try:
            proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return None, 'timeout'
        lines = proc.stdout.splitlines()
        if invoked_skill(lines, skill):
            return True, ''  # fired before any later failure (e.g. max turns)
        err = run_error(lines)
        if err or (proc.returncode != 0 and not lines):
            return None, err or (proc.stderr or 'claude exited with code %d' % proc.returncode)[:200]
        return False, ''


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--cases', default=str(ROOT / 'evals' / 'triggers.json'))
    ap.add_argument('--case', action='append', help='run only these case ids (repeatable)')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--runs', type=int, default=1)
    ap.add_argument('--model')
    ap.add_argument('--timeout', type=int, default=180)
    ap.add_argument('--json', help='write detailed results to this file')
    args = ap.parse_args()
    if not shutil.which('claude'):
        sys.exit('The Claude Code CLI (claude) is required.')
    spec = json.loads(Path(args.cases).read_text(encoding='utf-8'))
    cases = [c for c in spec['cases'] if not args.case or c['id'] in args.case][:args.limit]
    results, passed = [], 0
    for case in cases:
        hits, errors = 0, []
        for _ in range(args.runs):
            fired, err = run_case(case, spec['skill'], args.model, args.timeout)
            if err:
                errors.append(err)
            elif fired:
                hits += 1
        valid = args.runs - len(errors)
        rate = hits / valid if valid else None
        ok = rate is not None and (rate >= 0.5 if case['should_trigger'] else rate < 0.5)
        passed += ok
        results.append({**case, 'trigger_rate': rate, 'passed': ok, 'errors': errors})
        mark = 'PASS' if ok else 'FAIL'
        print(f"{mark}  {case['id']:<20} expected={'yes' if case['should_trigger'] else 'no ':<3} "
              f"fired={hits}/{valid}" + (f"  errors={len(errors)}" if errors else ''))
    print(f'\n{passed}/{len(cases)} cases passed')
    errs = sorted({e for r in results for e in r['errors']})
    if errs:
        print('Runs that failed before Claude could answer (not counted as skill behaviour):')
        for e in errs:
            print('  -', e)
    if args.json:
        Path(args.json).write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if passed == len(cases) else 1


if __name__ == '__main__':
    raise SystemExit(main())
