"""Release one plugin to its mirror repo, from this machine. Nothing runs on GitHub.

Steps, stopping at the first failure:
1. Refuse if the working tree is dirty, HEAD is not pushed, or the mirror
   already has a release for this version.
2. Run tools/gate.py for the plugin.
3. Vendor shared code with the mirror owner, so build_info.json names the
   mirror and the update check works. Rebuild, package with the owner as
   author, smoke test.
4. Create the mirror repo if missing (public, issues off), replace its files
   with the plugin folder, commit, tag v<version>, push.
5. Create a release on the mirror with the zip attached, and tag the monorepo
   <plugin-id>-v<version>.

The owner comes from the monorepo's origin remote. Nothing names an owner in source.

Usage: python tools/release.py <plugin-id> [--dry-run] [--skip-gate]
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COPY_IGNORE = shutil.ignore_patterns("node_modules", "dist", "out", "__pycache__", ".pytest_cache", "*.pyc")
SMOKE_FLAGS = {"qbittorrent-monitor": ["--mock-qbt"], "sabnzbd-monitor": ["--mock-sab"]}
DESCRIPTIONS = {
    "qbittorrent-monitor": "Decky Loader plugin: monitor and control qBittorrent from the Quick Access Menu. Mirror for releases.",
    "sabnzbd-monitor": "Decky Loader plugin: monitor and control SABnzbd from the Quick Access Menu. Mirror for releases.",
    "tuning-advisor": "Decky Loader plugin: read-only game tuning recommendations for handhelds. Mirror for releases.",
}


def sh(cmd: list[str], cwd: str = ROOT, capture: bool = False, check: bool = True) -> str:
    shell = os.name == "nt" and cmd[0] in ("pnpm", "npx")
    result = subprocess.run(cmd, cwd=cwd, stdin=subprocess.DEVNULL, shell=shell,
                            capture_output=capture, text=True)
    if check and result.returncode != 0:
        detail = (result.stderr or "").strip() if capture else ""
        raise SystemExit(f"FAILED: {' '.join(cmd[:3])} (exit {result.returncode}) {detail}")
    return (result.stdout or "").strip() if capture else ""


def owner_from_origin() -> str:
    url = sh(["git", "remote", "get-url", "origin"], capture=True)
    match = re.search(r"github\.com[:/]([^/]+)/", url)
    if not match:
        raise SystemExit(f"Cannot read the GitHub owner from origin: {url}")
    return match.group(1)


def preflight(plugin: str, version: str, mirror: str, dry_run: bool) -> None:
    problems = []
    if sh(["git", "status", "--porcelain"], capture=True):
        problems.append("The working tree has uncommitted changes. Commit or stash them first.")
    sh(["git", "fetch", "--quiet", "origin"])
    if sh(["git", "rev-parse", "HEAD"], capture=True) != sh(["git", "rev-parse", "origin/main"], capture=True):
        problems.append("HEAD is not the same as origin/main. Push first, so the release matches GitHub.")
    for problem in problems:
        if not dry_run:
            raise SystemExit(problem)
        print(f"dry run, would stop here: {problem}")
    exists = subprocess.run(["gh", "release", "view", f"v{version}", "--repo", mirror],
                            capture_output=True, text=True, stdin=subprocess.DEVNULL)
    if exists.returncode == 0:
        raise SystemExit(f"{mirror} already has release v{version}. Bump the version in plugins/{plugin}/package.json.")


def ensure_mirror(mirror: str, plugin: str, dry_run: bool) -> None:
    found = subprocess.run(["gh", "repo", "view", mirror, "--json", "name"], capture_output=True, text=True,
                           stdin=subprocess.DEVNULL)
    if found.returncode == 0:
        return
    print(f"creating {mirror}")
    if dry_run:
        return
    sh(["gh", "repo", "create", mirror, "--public", "--disable-issues", "--disable-wiki",
        "--description", DESCRIPTIONS.get(plugin, "Decky Loader plugin. Mirror for releases.")])
    # No checks run on GitHub, by the owner's decision. New repos start with Actions on.
    sh(["gh", "api", "-X", "PUT", f"repos/{mirror}/actions/permissions", "-F", "enabled=false"], capture=True)


def push_mirror(plugin: str, version: str, mirror: str, monorepo_sha: str, dry_run: bool) -> None:
    folder = os.path.join(ROOT, "plugins", plugin)
    work = tempfile.mkdtemp(prefix=f"mirror-{plugin}-")
    target = os.path.join(work, "repo")
    os.makedirs(target)
    sh(["git", "init", "--quiet", "-b", "main"], cwd=target)
    sh(["git", "remote", "add", "origin", f"https://github.com/{mirror}.git"], cwd=target)
    # Keep the mirror's history when it has any. A new or missing mirror starts empty.
    fetched = subprocess.run(["git", "fetch", "--quiet", "origin", "main"], cwd=target, capture_output=True,
                             stdin=subprocess.DEVNULL)
    if fetched.returncode == 0:
        sh(["git", "checkout", "--quiet", "-B", "main", "FETCH_HEAD"], cwd=target)
    for name in os.listdir(target):
        if name == ".git":
            continue
        path = os.path.join(target, name)
        shutil.rmtree(path) if os.path.isdir(path) else os.unlink(path)
    shutil.copytree(folder, target, ignore=COPY_IGNORE, dirs_exist_ok=True)
    shutil.copy2(os.path.join(ROOT, "LICENSE"), os.path.join(target, "LICENSE"))
    shutil.copy2(os.path.join(ROOT, ".gitattributes"), os.path.join(target, ".gitattributes"))
    sh(["git", "add", "-A"], cwd=target)
    changed = sh(["git", "status", "--porcelain"], cwd=target, capture=True)
    if changed:
        sh(["git", "-c", "user.name=" + git_config("user.name"), "-c", "user.email=" + git_config("user.email"),
            "commit", "--quiet", "-m", f"Release {plugin} {version}\n\nFrom the monorepo at {monorepo_sha[:7]}."],
           cwd=target)
    sh(["git", "tag", f"v{version}"], cwd=target)
    files = sh(["git", "ls-files"], cwd=target, capture=True).splitlines()
    print(f"mirror tree: {len(files)} files")
    for required in ("plugin.json", "package.json", "pnpm-lock.yaml", "main.py", "build_info.json", "LICENSE",
                     "py_modules/plugin_core/http.py", "src/shared/format.ts"):
        if required not in files:
            raise SystemExit(f"mirror tree is missing {required}")
    check_standalone(target)
    if dry_run:
        print(f"dry run: would push {mirror} main and v{version} from {target}")
        return
    sh(["git", "push", "--quiet", "origin", "main"], cwd=target)
    sh(["git", "push", "--quiet", "origin", f"v{version}"], cwd=target)


def check_standalone(target: str) -> None:
    """The mirror must build and pass its tests with no monorepo around it.
    node_modules and dist land in the mirror's .gitignore, so nothing extra is pushed."""
    print("checking the mirror builds on its own")
    sh(["pnpm", "install", "--frozen-lockfile", "--prefer-offline"], cwd=target, capture=True)
    sh(["pnpm", "test"], cwd=target, capture=True)
    sh(["pnpm", "build"], cwd=target, capture=True)
    sh(["pnpm", "typecheck"], cwd=target, capture=True)
    out = sh([sys.executable, "-m", "pytest", "-q", "-rs", "tests"], cwd=target, capture=True)
    summary = out.splitlines()[-1] if out else ""
    if "skipped" in summary:
        raise SystemExit(f"mirror tests skipped some tests, so they did not run standalone: {summary}")
    print(f"mirror standalone: {summary}")


def git_config(key: str) -> str:
    return sh(["git", "config", key], capture=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("plugin")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-gate", action="store_true", help="only after a gate run on this exact commit")
    args = parser.parse_args()
    plugin = args.plugin
    folder = os.path.join(ROOT, "plugins", plugin)
    if not os.path.isfile(os.path.join(folder, "plugin.json")):
        raise SystemExit(f"No plugin named {plugin}")
    with open(os.path.join(folder, "package.json"), encoding="utf-8") as handle:
        version = json.load(handle)["version"]
    owner = owner_from_origin()
    mirror = f"{owner}/{plugin}"
    sha = sh(["git", "rev-parse", "HEAD"], capture=True)
    print(f"releasing {plugin} {version} to {mirror} from {sha[:7]}" + (" (dry run)" if args.dry_run else ""))

    preflight(plugin, version, mirror, args.dry_run)
    py = sys.executable
    if not args.skip_gate:
        sh([py, "tools/gate.py", plugin])
    sh([py, "tools/vendor_shared.py", plugin, "--owner", owner])
    sh(["pnpm", "build"], cwd=folder)
    sh([py, "tools/package_zip.py", plugin, "--author", owner])
    sh([py, "-I", "tools/smoke_zip.py", f"out/{plugin}.zip", *SMOKE_FLAGS.get(plugin, [])])
    with open(os.path.join(folder, "build_info.json"), encoding="utf-8") as handle:
        info = json.load(handle)
    if info.get("repo") != mirror:
        raise SystemExit(f"build_info.json names {info.get('repo')!r}, expected {mirror!r}")

    ensure_mirror(mirror, plugin, args.dry_run)
    push_mirror(plugin, version, mirror, sha, args.dry_run)

    url = f"https://github.com/{mirror}/releases/latest/download/{plugin}.zip"
    notes = (f"{plugin} {version}, from {owner}/decky-plugins commit {sha[:7]}.\n\n"
             f"Install: Decky settings, General, turn on Developer mode. Then Developer, Install Plugin from URL:\n\n{url}")
    if args.dry_run:
        print(f"dry run: would create release v{version} on {mirror} and tag {plugin}-v{version} here")
        print(f"install URL: {url}")
        return 0
    sh(["gh", "release", "create", f"v{version}", f"out/{plugin}.zip", "--repo", mirror,
        "--title", f"{plugin} {version}", "--notes", notes])
    sh(["git", "tag", f"{plugin}-v{version}", sha])
    sh(["git", "push", "--quiet", "origin", f"{plugin}-v{version}"])
    print(f"released. Install URL: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
