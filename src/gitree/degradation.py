# todo: Handle degradation mode when GitHub API is rate-limited

import requests
from bs4 import BeautifulSoup
import re
from .base import _Connect
from .utils import lprint, cprint


class _Papyrus(_Connect):
    """"""
    _METADATA_NAME = "GiTreeMeta.json"
    _TAG_CLASS     = "a.Link--primary"
    def __init__(
            self,
            owner: str,
            repo: str,
            branch: str = "main",
            ua: str = "",
            timeout: int | float = 10.0
    ):
        """
        Args:
            owner (str):
                The owner of the repository to index.
            repo (str):
                The name of the repository to index.
            branch (str):
                default: "main"
                The branch of the repository to index.
            ua (str):
                default:
                    "Mozilla/5.0 (compatible; GiTreeSpider/0.0.1; +https://github.com/starwindv/gitree)"
                User agent string for requests.
            timeout (int|float):
                default: 10.0
                Timeout duration for requests.
        Raises:
            TypeError:
                If timeout is not a numeric type.
            ValueError:
                If timeout is a negative value.
        Returns:
            None
        """
        if not isinstance(timeout, (int, float)):
            raise TypeError(
                f"""
                    The _GiTree's arg `timeout` must be a number.(got `{type(timeout)}`)
                    """
            )
        if timeout < 0:
            raise ValueError(
                f"""
                    The _GiTree's arg `timeout` must greater than or equal(got `{timeout}`)
                    """
            )
        self.owner = owner
        self.repo = repo
        self.branch = branch
        self.pool = requests.Session()
        self.meta = []
        self.data = None
        if ua:
            self._UA = ua
        self._build()
        self.timeout = timeout

    def _build(self):
        self._WEB_URL = (
            self._WEB_URL
            .replace(";owner;", self.owner)
            .replace(";repo;", self.repo)
            .replace(";branch;", self.branch)
        )
        self.headers = {
            "User-Agent": self._UA
        }

    def _capture_a(self, url: str = "")->set:
        try:
            if url == "":
                url = self._WEB_URL
            response = self.pool.get(
                url,
                headers = self.headers,
                timeout = self.timeout,
                stream = True
            )
            response.raise_for_status()
            soup = BeautifulSoup(
                response.text,
                "html.parser"
            )
            links = soup.select(self._TAG_CLASS)
            links = [str(link) for link in links.copy()]
            return set(re.sub("<span.*</span>", "", x) for x in links)
        except requests.exceptions.RequestException as e:
            lprint(f"Failed when get page: {url}", prefix="[Err ]")
            cprint(f";#ffbf00;[ErrL] {repr(e)}")
            return set()

    def _pre_process_a(self, url: str = "")->list:
        if url == "":
            url = self._WEB_URL
        original_data = self._capture_a(url)
        return [x for x in original_data if (">Packages\n" not in x) and (">Releases</a>" not in x)]

    def _process_a(self, url: str = "")->list[dict]:
        if url == "":
            url = self._WEB_URL
        pre_processed_data = self._pre_process_a(url)
        pattern = r'href="(.*?)"|aria-label=".*?\((.*?)\)"|>(.*?)<'
        result = []
        for item in pre_processed_data:
            matches = re.findall(pattern, item)
            href = next(m[0] for m in matches if m[0])
            file_type = next(m[1] for m in matches if m[1])
            name = next(m[2] for m in matches if m[2])

            result.append({
                "name": name,
                "is_file": file_type == "File",
                "url": f"{self._DOMAIN_URL}{href}"
            })
        return result

    def _process(self, url: str = ""):
        data = self._process_a(url=url)
        self.meta += data
        self.waiting_dir = dict()
        self.files = dict()
        for element in self.data:
            is_file = self.data.get("is_file", False)

    def _loop(self):
        if self.data is None:
            self._process()

# """
# [
#     '<a aria-label="box, (Directory)" class="Link--primary"
# data-discover="true" href="/StarWindv/StarWindv/tree/main/box"
# title="box">box</a>',
#     '<a aria-label="README.md, (File)" class="Link--primary"
# data-discover="true" href="/StarWindv/StarWindv/blob/main/README.md"
# title="README.md">README.md</a>'
# ]
#
# [↓]
#
# {
#     "name"   : str,
#     "is_file": bool,
#     "url"    : "https://github.com" + href,
# },{...}
#
# [↓]
#
# [
#     {
#         'name': 'box',
#         'is_file': False,
#         'url': 'https://github.com/StarWindv/StarWindv/tree/main/box'
#     },
#     {
#         'name': 'README.md',
#         'is_file': True,
#         'url': 'https://github.com/StarWindv/StarWindv/blob/main/README.md'
#     }
# ]
# """
