#!/usr/bin/env python3

import sys
import subprocess
import requests
import importlib.metadata
import ctypes
import os
import re
import urllib.parse
from datetime import datetime
from .constants import POPULAR_PACKAGES


_SPEC_RE = re.compile(
    r'^([A-Za-z0-9][A-Za-z0-9._-]{0,213})'
    r'(?:\[[A-Za-z0-9,_-]+\])?'
    r'(?:[<>=!~][^\s;]+)?$'
)


def parse_package_spec(spec):
    m = _SPEC_RE.match(spec)
    return m.group(1) if m else None


# Load the library using an absolute path to avoid more "File Not Found" errors
def get_lib_path():
    # Dynamically finds the compiled C library.
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # We broaden the search to find any file with 'distance' in the name.
    # .pyd is the suffix used on Windows.
    for file in os.listdir(current_dir):
        if "distance" in file and file.endswith((".so", ".dylib", ".pyd")):
            return os.path.join(current_dir, file)
    return None

# Load the library using the dynamic path
lib_path = get_lib_path()

if lib_path:
    try:
        distance_lib = ctypes.CDLL(lib_path)
        distance_lib.levenshtein.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
        distance_lib.levenshtein.restype = ctypes.c_int
    except OSError as e:
        print(f"OS Error loading library: {e}")
        distance_lib = None
else:
    print("Could not find compiled distance_lib. Running without typo detection.")
    distance_lib = None

def get_edit_distance(str1, str2):
    if not distance_lib:
        return 999 # Fallback
    # Strings must be encoded to bytes for C
    return distance_lib.levenshtein(str1.encode('utf-8'), str2.encode('utf-8'))

def is_installed(package_name):
    try:
        # This checks the metadata of your current environment (if already installed)
        importlib.metadata.version(package_name)
        return True
    except importlib.metadata.PackageNotFoundError:
        return False

def get_github_stats(info):
    urls = info.get('project_urls', {})
    if not urls:
        return None

    # Look for a GitHub link in the values
    github_url = None
    for url in urls.values():
        if 'github.com' in url.lower():
            github_url = url
            break

    if not github_url:
        return None

    # Use regex to find "owner/repo"
    match = re.search(r'github\.com/([^/]+)/([^/?#]+)', github_url)
    if not match:
        return None

    owner, repo = match.groups()
    if repo.endswith('.git'):
        repo = repo[:-4]

    api_url = f"https://api.github.com/repos/{owner}/{repo}"
    try:
        # Note: GitHub API has rate limits for unauthenticated calls
        resp = requests.get(api_url, timeout=3)
    except requests.RequestException:
        return None

    if resp.status_code != 200:
        return None
    data = resp.json()
    return {
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "issues": data.get("open_issues_count", 0),
    }

def vet_package(package_name):
    # Typo Detection using C
    # 1. Collect all potential matches first via C engine
    matches = [target for target in POPULAR_PACKAGES
               if get_edit_distance(package_name, target) <= 2]

    if len(matches) == 1:
        # Simple case: Only one match
        target = matches[0]
        print(f"\nALERT: You typed '{package_name}'.")
        print(f"Did you mean the official '{target}' package?")
        if input(f"Switch to '{target}'? (y/n): ").lower() == 'y':
            package_name = target
    elif len(matches) > 1:
        # 2. Multi-match case: Offer the [y]es, [n]o, [a]ll menu
        target = matches[0]
        print(f"\nALERT: You typed '{package_name}'.")
        print(f"First match: '{target}'")
        choice = input(f"Switch to '{target}'? [y]es / [n]o / see [a]ll {len(matches)} matches: ").lower()

        if choice == 'y':
            package_name = target
        elif choice == 'a':
            # 3. Display the numbered menu
            print(f"\nAll potential matches for '{package_name}':")
            for idx, name in enumerate(matches, 1):
                print(f"{idx}) {name}")

            try:
                selection = input(f"\nSelect a number (1-{len(matches)}) or 'c' to cancel: ")
                if selection.lower() == 'c':
                    return False, package_name

                selected_idx = int(selection) - 1
                if 0 <= selected_idx < len(matches):
                    package_name = matches[selected_idx]
            except ValueError:
                print("Invalid input. Proceeding with original name.")

    print(f"Querying PyPI for '{package_name}'")
    url = f"https://pypi.org/pypi/{urllib.parse.quote(package_name, safe='')}/json"

    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException as e:
        print(f"Network error: {e}")
        return False, package_name

    if response.status_code == 404:
        print(f"ERROR: Package '{package_name}' not found")
        return False, package_name

    data = response.json()
    info = data.get('info', {})

    # Get package Description/Summary
    summary = info.get('summary', 'No description provided.')

    # Look through all the releases, list starting at original release and then updates
    releases = data.get('releases', {})
    v_list = list(releases.keys())

    # Check if v_list exists AND the first version has upload data (prevent empty packages from causing problems)
    if v_list and len(releases[v_list[0]]) > 0:
        created_raw = releases[v_list[0]][0].get('upload_time', "Unknown")
    else:
        created_raw = "Unknown"

    # Check if 'urls' exists and has at least one entry (most recent update)
    urls = data.get('urls', [])
    if urls:
        last_upload_raw = urls[0].get('upload_time_iso_8601', "Unknown")
    else:
        last_upload_raw = "Unknown"

    # Display Report
    print(f"Vetting {package_name.upper()}: ")
    print(f"Description: {summary}")
    print(f"Author: {info.get('author', 'Unknown')}")
    print(f"Created: {created_raw[:10]}")
    print(f"Last Updated: {last_upload_raw[:10]}")

    # GitHub Check
    stats = get_github_stats(info)
    if stats:
        print("\nGitHub Stats:")
        print(f"Stars: {stats['stars']}")
        print(f"Forks: {stats['forks']}")
        print(f"Issues: {stats['issues']}")
    else:
        print("WARNING: No GitHub repository linked")

    # Security Warning Logic
    if "T" in last_upload_raw:
        updated_dt = datetime.fromisoformat(last_upload_raw.replace('Z', '+00:00'))
        days_ago = (datetime.now(updated_dt.tzinfo) - updated_dt).days
        if days_ago < 7:
            print(f"CAUTION: This package was updated very recently - ({days_ago} days ago)")

    confirm = input(f"\nProceed with installation? (y/n): ")
    return confirm.lower() == 'y', package_name


def main():
    if len(sys.argv) < 2:
        print("Usage: safepip <package_name>")
        sys.exit(1)

    spec = sys.argv[1]
    name = parse_package_spec(spec)
    if not name:
        print(f"Invalid package specifier: {spec!r}")
        print("Expected something like 'requests' or 'requests==2.31.0'.")
        sys.exit(1)

    proceed, final_name = vet_package(name)
    if not proceed:
        sys.exit(1)

    # Preserve version pins/extras from the original spec unless the user
    # accepted a typo correction, in which case install the corrected name.
    install_target = final_name if final_name != name else spec

    if is_installed(final_name):
        current_version = importlib.metadata.version(final_name)
        print(f"'{final_name}' (v{current_version}) is already installed.")
        if input("Do you want to force reinstall/update? (y/n): ").lower() != 'y':
            sys.exit(0)

    print(f"Launching pip install {install_target}...", flush=True)
    result = subprocess.run([sys.executable, "-m", "pip", "install", install_target])
    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
