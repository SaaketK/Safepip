# Safepip

Safepip is a security-focused wrapper for the Python package installer (pip). It introduces a vetting layer designed to protect developers from typosquatting attacks and malicious package injections by analyzing metadata and performing local heuristic checks before any installation occurs.

## Key Features

- **C-Powered Typo Detection:** Utilizes a custom Levenshtein Distance engine written in C for high-performance string comparison against popular packages.
- **Automated Intelligence Updates:** Includes a dedicated utility to synchronize the local security watchlist with the latest top 1,000 PyPI packages.
- **Metadata Inspection:** Retrieves and displays package summaries, author information, and creation dates directly from the PyPI JSON API.
- **GitHub Integration:** Fetches repository statistics (stars, forks, open issues) to help gauge the reputation of the software source.
- **Security Heuristics:** Flags packages that have been updated within the last seven days to alert users of potential "release hijacking" risks.

## Installation

To install Safepip for development and local use:

1. Clone the repository:
   git clone https://github.com/SaaketK/Safepip.git

2. Navigate to the project directory:
   cd safepip

3. Install the package in editable mode:
   pip install -e .

The installation process automatically compiles the C-extension (`distance_lib`) and maps the command-line entry points.

## Usage

### Vetting and Installing Packages
Use the `safepip` command followed by the name of the package you wish to inspect:

safepip <package_name>

Example:
safepip gunicor

If a typo is detected (e.g., 'gunicor' instead of 'gunicorn'), the tool will prompt you to switch to the official package before proceeding.

### Updating the Security Watchlist
To ensure the typo detection engine is checking against the most current high-traffic packages, run the update utility:

safepip-update

## How It Works

### The C-Extension Engine
The core logic for string comparison resides in `src/safepip/distance.c`. By offloading the Levenshtein Distance calculation to a compiled C library, Safepip can iterate through the top 1,000 most popular packages in a fraction of a millisecond. Python interfaces with this binary using the `ctypes` library, which dynamically loads the `.so` or `.dylib` file at runtime.

### Automated Constants Synchronization
The `safepip-constupdate` command executes a maintenance script that performs the following steps:
1. Connects to the hugovk.dev PyPI stats API.
2. Extracts the top 1,000 project names by download volume.
3. Overwrites `src/safepip/constants.py` with the fresh data.
This allows the security heuristics to remain effective against the ever-changing landscape of popular Python software.

### The Vetting Pipeline
When a package name is provided:
1. **Local Check:** The string is cross-referenced with the popular package list via the C engine.
2. **Network Query:** If no typo is suspected or the user proceeds, Safepip queries the PyPI JSON API.
3. **Reputation Analysis:** The tool calculates the age of the release and attempts to locate the linked GitHub repository to pull live health metrics.
4. **Execution:** Only after explicit user confirmation does the tool invoke `subprocess` to run the actual `pip install` command.

## Project Structure

- `src/safepip/main.py`: The primary entry point and application logic.
- `src/safepip/distance.c`: The C implementation for edit-distance algorithms.
- `src/safepip/update_constants.py`: The synchronization utility for the watchlist.
- `src/safepip/constants.py`: The data store for the top 1,000 package names.
- `pyproject.toml`: Defines the build system and command-line entry points.
