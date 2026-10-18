"""GhostEnv CLI.

  ghostenv scan    <project> [--json]
  ghostenv check   <project> [--json] [--env-file f] [--example-file f]
  ghostenv example <project> [-o path] [--stdout] [--force]
                             [--env-file f] [--example-file f]

Exit codes: 0 = contract complete / action done, 1 = blocking
findings (names missing with no default, a missing example file,
case mismatches, duplicates, malformed lines; the verdict names
exactly which), 2 = could not scan / refused. Soft and stale
findings never block. ``scan`` and ``check`` never write.
``example`` writes only the file named (or the project example file
with --force when it already exists). Values are never printed,
logged, or stored on any path: names + present/absent only.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .doctor import build_report
from .examplegen import names_for_example, render_example
from .reports import render_scan_text, render_text


def _report_or_error(args):
    project = Path(args.project)
    if not project.is_dir():
        print(f"error: project not found: {project}", file=sys.stderr)
        return None
    return build_report(project,
                        env_file=getattr(args, "env_file", None),
                        example_file=getattr(args, "example_file", None))


def cmd_scan(args) -> int:
    report = _report_or_error(args)
    if report is None:
        return 2
    if args.json:
        print(json.dumps({
            "tool": report["tool"], "version": report["version"],
            "project": report["project"],
            "names_only_statement": report["names_only_statement"],
            "used_in_code": report["sets"]["used_in_code"],
            "usages": report["usages"],
            "dynamic_sites": report["dynamic_sites"],
            "files_scanned": report["counts"]["files_scanned"],
        }, indent=2))
    else:
        print(render_scan_text(report))
    return 0


def cmd_check(args) -> int:
    report = _report_or_error(args)
    if report is None:
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_text(report))
    return int(report["exit_code"])


def cmd_example(args) -> int:
    report = _report_or_error(args)
    if report is None:
        return 2
    content = render_example(names_for_example(report))
    if args.stdout:
        print(content, end="")
        return 0
    project = Path(args.project)
    if args.output:
        target = Path(args.output)
    elif args.example_file:
        target = Path(args.example_file)
    else:
        target = project / ".env.example"
    if target.exists() and not args.force and not args.output:
        print(f"error: {target} already exists; pass --force to "
              f"overwrite or -o <path> to write elsewhere",
              file=sys.stderr)
        return 2
    try:
        target.write_text(content, encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write {target}: {exc}", file=sys.stderr)
        return 2
    print(f"Wrote {target} "
          f"({len(names_for_example(report))} names, values never "
          f"included)")
    return 0


def _add_files(p):
    p.add_argument("--env-file", help="path to the .env file "
                                      "(default: <project>/.env)")
    p.add_argument("--example-file", help="path to the example file "
                                          "(default: first of "
                                          ".env.example/.env.sample/"
                                          ".env.template)")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="ghostenv",
        description="Local .env doctor: env var names used in code vs "
                    "defined in .env vs documented in .env.example. "
                    "Names only - values are never read into output.")
    parser.add_argument("--version", action="version",
                        version=f"ghostenv {__version__}")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("scan", help="list env var names used in code")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_scan)

    p = sub.add_parser("check", help="compare code / .env / example "
                                     "name sets and classify drift")
    p.add_argument("project")
    p.add_argument("--json", action="store_true")
    _add_files(p)
    p.set_defaults(fn=cmd_check)

    p = sub.add_parser("example", help="generate a clean, names-only "
                                       ".env.example")
    p.add_argument("project")
    p.add_argument("-o", "--output", help="write here instead of "
                                          "<project>/.env.example")
    p.add_argument("--stdout", action="store_true",
                   help="print to stdout instead of writing a file")
    p.add_argument("--force", action="store_true",
                   help="overwrite an existing example file")
    _add_files(p)
    p.set_defaults(fn=cmd_example)

    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
