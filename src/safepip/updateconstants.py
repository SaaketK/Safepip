import re
import requests
import os

_NAME_RE = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._-]{0,213}$')


def update_top_packages(count=1000):
    url = "https://hugovk.dev/top-pypi-packages/top-pypi-packages.min.json"
    print(f"Fetching top {count} packages from hugovk.dev...")

    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Validate names before writing, the watchlist is compared against
        # user input so a malformed entry would turn into a bad suggestion.
        top_names = [
            row['project'] for row in data['rows'][:count]
            if _NAME_RE.match(row.get('project', ''))
        ]

        # Use the directory where THIS script lives
        current_dir = os.path.dirname(os.path.abspath(__file__))
        target_path = os.path.join(current_dir, "constants.py")

        # Format the data into a Python file
        with open(target_path, "w") as f:
            f.write("# Auto-generated constants file\n")
            f.write(f"# Source: {url}\n\n")
            f.write("POPULAR_PACKAGES = [\n")
            for name in top_names:
                f.write(f'    "{name}",\n')
            f.write("]\n")

        print(f"Successfully updated constants.py with {len(top_names)} packages.")

    except Exception as e:
        print(f"Failed to update packages: {e}")


if __name__ == "__main__":
    update_top_packages(1000)