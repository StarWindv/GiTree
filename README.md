# GiTree - GitHub Repository Downloader

![GitHub License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)

GiTree is a Python utility that enables you to download entire GitHub repositories while preserving their directory structure. It efficiently traverses repository contents and downloads files using parallel processing for optimal performance.

## Key Features

- **Complete Repository Download**: Downloads entire repositories including all files and directories
- **Parallel Processing**: Uses multi-threading for faster downloads of large repositories
- **Configurable**: Customize download behavior through configuration settings
- **Progress Tracking**: Provides real-time progress updates during downloads
- **Error Handling**: Robust error reporting for failed downloads
- **Branch Support**: Download specific repository branches

## Installation

```bash
pip install gitree
```

## Usage

### Basic Example

```python
from gitree import GiTree

# Initialize with repository details
downloader = GiTree(
    owner="owner_name",
    repo="repository_name",
    branch="main"  # Optional, defaults to "main"
)

# Download repository contents
downloader.gets()
```

### Advanced Configuration

```python
downloader = GiTree(
    owner="owner_name",
    repo="repository_name",
    branch="dev",              # Specify branch
    save_path="~/custom_path", # Custom save location
    when_to_thread=10,         # Enable threading for >10 files
    chunk_size=2048,           # Set download chunk size
    timeout=15.0,              # Set request timeout
    ua="Custom User Agent"     # Set custom user agent
)
```

## Configuration

GiTree automatically creates a configuration file at `~/.stv_project/GiTree/GiTree.json` with these default settings:

```json
{
    "download": true,
    "save_path": "~/.stv_project/GiTree/repo",
    "when_to_thread": 6
}
```

You can modify these values directly in the configuration file to change default behavior.

## Command Line Interface
- [ ] this mode is under development.
```bash
gitree --owner OWNER --repo REPO [--branch BRANCH] [--path SAVE_PATH]
```

## Requirements

- Python 3.10+
- Dependencies:
  - `requests`
  - `rich` (for formated output)
  - `stv_utils==0.0.7` (a lightweight hex colored print)

## License

GiTree is licensed under the GNU General Public License v3.0 (GPLv3). See the [LICENSE](https://www.gnu.org/licenses/gpl-3.0.en.html) file for details.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements.

## Support

For issues or feature requests, please [open an issue](https://github.com/StarWindv/GiTree/issues) on GitHub.

---

**Note**: This tool respects GitHub's API rate limits. Please use responsibly and avoid excessive requests.
