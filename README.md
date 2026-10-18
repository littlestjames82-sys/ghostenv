# GhostEnv

**Are the names your code needs the names your .env actually has?**

Projects break in a boring, expensive way: code starts reading a
new environment variable, nobody adds it to `.env.example`, and
the next person (or the next agent run) finds out at runtime.
GhostEnv is the doctor for that. It compares three name sets:

1. names the code uses (`os.environ` / `os.getenv` in Python,
   `process.env` in JS/TS, and similar patterns),
2. names defined in `.env`,
3. names documented in `.env.example`,

and reports the differences: used but not defined, used but not
documented, documented but no longer used, defined but never used,
duplicated, case-mismatched spellings of the same name, and
malformed lines.

**Names only, never values.** GhostEnv reads values only far
enough to know a line is shaped like `NAME=...`. No report, no
generated file, and no log line ever contains a value from a
`.env`. That rule is enforced by a dedicated leak test with a
planted fake canary value: if the canary ever appears in any
output, the suite fails.

It can also generate a clean `.env.example`: every used and
defined name, with empty placeholder values, ready to commit.

By Ghost Developer Studio. MIT core. Zero dependencies: Python
standard library only, local-first, no network, no telemetry.

Position in the Ghost stack: GhostSlice governs what an agent
reads, GhostExposure records what a sensitive bundle contains,
GhostEnv governs whether a project's environment contract is
documented and consistent. Agent Seatbelt still governs what an
agent does.

## Install

```bash
cd ghostenv
pip install .
ghostenv --help
```

Or run from a checkout without installing:

```bash
PYTHONPATH=src python3 -m ghostenv --help
```

Requires Python 3.10 or newer. The shipped CLI's `--help` is the
authority for exact subcommand spelling; the common shapes are:

## Quickstart

```bash
# Check a project: code usage vs .env vs .env.example
ghostenv check ~/my-project
echo $?   # 0 = no blocking findings, 1 = blocking findings
          # (the verdict line names exactly which), 2 = could
          # not scan

# Generate a clean .env.example (names + empty placeholders)
ghostenv example ~/my-project -o ~/my-project/.env.example.new
# Review it, then rename it over the old example. GhostEnv never
# modifies your real .env.
```

A worked walkthrough lives in [`examples/`](examples/README.md).

## What it reports

| Finding | Meaning |
|---|---|
| used, missing from `.env` | Code reads a name nothing defines locally. It will fall back to a default or crash. |
| used, missing from `.env.example` | The contract is undocumented. The next checkout will not know to set it. |
| in `.env.example`, not used | Stale documentation, or a name used outside scanned code (say so in a comment). |
| in `.env`, not used | Possibly dead, possibly set for a tool the scanner does not read. Evidence, not proof. |
| duplicate name | The same name defined twice in one file. Which one wins depends on the loader. |
| case mismatch | The same name spelled with different case in different places (`Api_Url` in code, `API_URL` in `.env`). On case-sensitive systems those are different variables. |
| malformed line | A line that is neither blank, comment, nor `NAME=...`. Reported by file and line number only; the line's content is never shown, because it may be a bare value. |

Blocking findings fail the check (exit 1): a used name missing
from `.env` with no default at any read site, a missing example
file, a case mismatch, a duplicate, or a malformed line. The
verdict line names exactly which blocking findings fired. Soft
findings (every read site has a default), stale entries, and a
name missing from an example file that exists are reported but
do not block on their own.

## The names-only rule, stated plainly

- Reports contain variable names, file paths, and line numbers.
- Reports never contain values, prefixes of values, or hashes of
  values.
- A generated `.env.example` contains names with empty values or
  clearly labelled placeholders only.
- The test suite plants a unique fake canary value in a fixture
  `.env` and asserts it appears in no stdout, stderr, report, or
  generated file, ever.

## Limits

- Static scanning finds name usage in the patterns it knows.
  Dynamic lookups (`os.environ[some_variable]`, computed names,
  f-string names, reflection) cannot be resolved: the scan
  counts them as dynamic read sites by file and line, and the
  names they read stay invisible to the report.
- Reads mentioned in full-line comments are not counted, and
  reads inside string literals can be counted. Parser-lite,
  labelled as such.
- A clean check is evidence that the three name sets agree. It
  is not proof an application will run: values can still be
  wrong, empty, or point at the wrong place, and GhostEnv
  deliberately never inspects them.
- Frameworks and deployment platforms inject names code never
  mentions. Treat an unused or undocumented finding as a prompt
  to document, not an automatic fault.

## Out of scope for v0.1

- Reading, storing, syncing, or validating secret values.
- Writing to a real `.env` (generation targets an example file).
- Cloud secret managers, accounts, telemetry, paid layer.

## Tests

```bash
python3 -m pytest tests -q
# or
python3 -m unittest discover -s tests
```

The suite is black-box: fixture tests always run; CLI tests drive
the shipped CLI (discovered from `--help`) and skip cleanly if no
CLI is present yet. It includes planted-missing-name fixtures, a
malformed `.env` fixture, and the canary leak test described
above.

## Layout

```
src/ghostenv/   the tool (Agent A)
tests/          black-box suite + fixtures (names + fake values only)
examples/       mini project walkthrough, fake placeholders only
PLAN.md         the v0.1 plan
```
