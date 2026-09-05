# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml>=6.0"]
# ///
"""Resolve a declared dependency floor to the highest tagged release.

data/dependencies.yaml declares what this repository builds on in the
marketplace's shape: a name, the repository that publishes it, and a
version floor such as ">=2026.9.2" (an optional ceiling, "<2027",
narrows it). This tool lists the repository's release tags with
`git ls-remote --tags`, keeps the ones named {name}--v{version}, drops
every version outside the declared range, and prints the highest one
with the commit it points at. CI checks that commit out, so what runs
there is a signed, tagged release chosen by the floor this repository
declares, not a branch and not a hand-moved pin.

Versions compare as tuples of integers (2026.9.10 is newer than
2026.9.9). Annotated tags are peeled to the commit (the `^{}` entry);
a lightweight tag is its own commit. A repository with no tag in range
fails the run: the floor says what this repository needs, and nothing
published meets it.

Usage:
  resolve_release.py DEPENDENCIES.yaml NAME [--github-output PATH]
  resolve_release.py --selftest

With --github-output the tool appends `ref=<tag>` and `commit=<sha>`
to that file itself, so the workflow reads the outputs from the step
and no shell substitution swallows a failing exit status.
"""

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

RANGE_TERM = re.compile(r"^\s*(>=|<=|<|>|==)\s*v?(\d+(?:\.\d+)*)\s*$")


def parse_version(text: str) -> tuple[int, ...]:
    return tuple(int(p) for p in text.split("."))


def parse_range(spec: str):
    """">=2026.9.2" or ">=2026.9.2,<2027" into a list of (op, version)."""
    terms = []
    for raw in spec.split(","):
        m = RANGE_TERM.match(raw)
        if not m:
            raise ValueError(f"unreadable version range term: {raw!r}")
        terms.append((m.group(1), parse_version(m.group(2))))
    return terms


def satisfies(version: tuple[int, ...], terms) -> bool:
    ops = {
        ">=": lambda v, w: v >= w,
        ">": lambda v, w: v > w,
        "<=": lambda v, w: v <= w,
        "<": lambda v, w: v < w,
        "==": lambda v, w: v == w,
    }
    return all(ops[op](version, want) for op, want in terms)


def parse_ls_remote(text: str, name: str) -> dict[str, tuple[tuple[int, ...], str]]:
    """ls-remote output into {tag: (version, commit)}, peeled commit
    preferred over the tag object's own sha."""
    prefix = f"refs/tags/{name}--v"
    tags: dict[str, tuple[tuple[int, ...], str]] = {}
    peeled: dict[str, str] = {}
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) != 2 or not parts[1].startswith(prefix):
            continue
        sha, ref = parts
        is_peeled = ref.endswith("^{}")
        tag = ref[len("refs/tags/"):-3] if is_peeled else ref[len("refs/tags/"):]
        version_text = tag[len(f"{name}--v"):]
        if not re.fullmatch(r"\d+(\.\d+)*", version_text):
            continue
        if is_peeled:
            peeled[tag] = sha
        else:
            tags[tag] = (parse_version(version_text), sha)
    return {t: (v, peeled.get(t, sha)) for t, (v, sha) in tags.items()}


def choose(tags, terms):
    """The highest tag in range, or None."""
    in_range = [(v, t, c) for t, (v, c) in tags.items() if satisfies(v, terms)]
    if not in_range:
        return None
    v, t, c = max(in_range)
    return t, c


def ls_remote(repository: str) -> str:
    url = f"https://github.com/{repository}"
    out = subprocess.run(["git", "ls-remote", "--tags", url],
                         check=True, capture_output=True, text=True)
    return out.stdout


def load_dependency(path: Path, name: str) -> dict:
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for dep in doc.get("dependencies", []):
        if dep.get("name") == name:
            for key in ("repository", "version"):
                if key not in dep:
                    raise ValueError(f"dependency {name} lacks {key}")
            return dep
    raise ValueError(f"no dependency named {name} in {path}")


def resolve(dep: dict, listing: str):
    terms = parse_range(dep["version"])
    tags = parse_ls_remote(listing, dep["name"])
    pick = choose(tags, terms)
    return pick, len(tags)


# --- selftest: canned ls-remote output, no network

def selftest() -> int:
    listing = "\n".join([
        "aaaa\trefs/heads/main",
        "1111\trefs/tags/nasa-daac-knowledge--v2026.9.1",
        "2222\trefs/tags/nasa-daac-knowledge--v2026.9.1^{}",
        "3333\trefs/tags/nasa-daac-knowledge--v2026.9.2",
        "4444\trefs/tags/nasa-daac-knowledge--v2026.9.2^{}",
        "5555\trefs/tags/nasa-daac-knowledge--v2026.9.10",
        "6666\trefs/tags/other-plugin--v9.9.9",
        "7777\trefs/tags/nasa-daac-knowledge--vnext",
        "8888\trefs/tags/v2027.1.0",
    ])
    results = []

    def check(label, cond):
        results.append((label, cond))
        print(("ok   " if cond else "FAIL ") + label)

    dep = {"name": "nasa-daac-knowledge", "version": ">=2026.9.2"}
    pick, n = resolve(dep, listing)
    check("only tags named {name}--v{version} are read", n == 3)
    check("numeric ordering: 2026.9.10 beats 2026.9.2",
          pick == ("nasa-daac-knowledge--v2026.9.10", "5555"))
    check("lightweight tag resolves to its own sha", pick[1] == "5555")

    pick, _ = resolve({"name": "nasa-daac-knowledge", "version": ">=2026.9.2,<2026.9.10"}, listing)
    check("ceiling narrows the range and the peeled sha is preferred",
          pick == ("nasa-daac-knowledge--v2026.9.2", "4444"))

    pick, _ = resolve({"name": "nasa-daac-knowledge", "version": ">=2027"}, listing)
    check("no tag in range resolves to nothing", pick is None)

    pick, _ = resolve({"name": "nasa-daac-knowledge", "version": "==2026.9.1"}, listing)
    check("exact pin still works", pick == ("nasa-daac-knowledge--v2026.9.1", "2222"))

    try:
        parse_range(">=main")
        check("a branch name is not a version range", False)
    except ValueError:
        check("a branch name is not a version range", True)

    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "dependencies.yaml"
        p.write_text("dependencies:\n  - name: x\n    repository: o/x\n"
                     "    version: '>=1'\n", encoding="utf-8")
        d = load_dependency(p, "x")
        check("declaration file reads back", d["repository"] == "o/x")
        try:
            load_dependency(p, "y")
            check("an undeclared name fails", False)
        except ValueError:
            check("an undeclared name fails", True)
        out = Path(td) / "out.txt"
        write_outputs(out, "x--v1.2.3", "abc")
        check("github output lines written",
              out.read_text() == "ref=x--v1.2.3\ncommit=abc\n")

    if all(c for _, c in results):
        print(f"PASS resolve_release selftest ({len(results)} checks)")
        return 0
    print("FAIL resolve_release selftest")
    return 1


def write_outputs(path: Path, tag: str, commit: str) -> None:
    with path.open("a", encoding="utf-8") as f:
        f.write(f"ref={tag}\ncommit={commit}\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("declaration", nargs="?", type=Path)
    ap.add_argument("name", nargs="?")
    ap.add_argument("--github-output", type=Path,
                    help="append ref= and commit= lines to this file")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.declaration or not args.name:
        ap.error("DEPENDENCIES.yaml and NAME are required")
    dep = load_dependency(args.declaration, args.name)
    pick, n = resolve(dep, ls_remote(dep["repository"]))
    if pick is None:
        print(f"FAIL: no release of {dep['name']} in {dep['repository']} "
              f"satisfies {dep['version']} ({n} release tags listed)")
        return 1
    tag, commit = pick
    print(f"{tag} (commit {commit[:7]}) is the highest of {n} release "
          f"tags satisfying {dep['version']}")
    if args.github_output:
        write_outputs(args.github_output, tag, commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
