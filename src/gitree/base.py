from .utils import lprint
import os
import json


class _Connect:
    """
    This is a base class,
    which defined some base url for GitHub.
    """
    _BASE_URL = "https://api.github.com/repos/;owner;/;repo;/contents?ref=;branch;"
    _RAW_UEL = "https://raw.githubusercontent.com/;owner;/;repo;/;branch;/;path;"
    _UA = "Mozilla/5.0 " + \
          "(compatible; GiTreeSpider/0.0.1; " + \
          "+https://github.com/starwindv/gitree)"


class Configer:
    """
    This is config manager, which can load config file and parse it.
    """
    _Config = "~/.stv_project/GiTree/GiTree.json"
    DefaultSavePath = "~/.stv_project/GiTree/repo"

    def __init__(self):
        self.data = None
        self._load()

    def parse(self, key: str, force: bool = False):
        """
        Retrieves configuration value for a specified key.

        Args:
            key: Configuration key to retrieve value for.
            force: If True, forces reload of configuration before lookup.
                Defaults to False.

        Returns:
            Value associated with the key, or empty string if key not found.
        """
        if force:
            self._load()
        return self.data.get(key, "")

    def _load(self, force: bool = False)->None:
        """

        Args:
            force (bool): If this arg is `True`, then program while reload config everytime.

        Returns: None

        """
        if self.data is None or force:
            config_path = os.path.expanduser(self._Config)
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            try:
                with open(config_path, 'r+', encoding='utf-8') as f:
                    self.data = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                with open(config_path, 'w', encoding='utf-8') as f:
                    lprint(
                        f"The GiTree's default save path at: ;ff4433;{self.DefaultSavePath}"
                    )
                    lprint(f"The GiTree's config file at      : ;ff4433;{self._Config}")
                    self.data = {
                        "download": True,
                        "save_path": self.DefaultSavePath,
                        "when_to_thread": 6
                    }
                    f.write(
                        json.dumps(
                            self.data,
                            ensure_ascii=True,
                            indent=4
                        )
                    )