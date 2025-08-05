import requests
import json
from typing import Callable, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from requests import Response
from rich import print
from pathlib import Path
import os
from stv_utils import print as cprint


def lprint(
        *values,
        prefix: str = "[INFO]",
        **kwargs
):
    """
    Prints colored messages to the console based on prefix type.

    Args:
        *values: Variable length argument list to print.
        prefix: Message prefix indicating message type. Defaults to "[INFO]".
            Valid options: "[INFO]", "[Warn]", "[Err]".
        **kwargs: Arbitrary keyword arguments passed to the underlying print function.

    Notes:
        - Uses color coding for different message types:
            [INFO]: Green (#AFE1AF)
            [Warn]: Yellow (#E4D00A)
            [Err]: Red (#DC143C)
            Default: Cadet blue (#5F9EA0)
        - Formats output using `cprint` from stv_utils
    """
    info_c = ";#AFE1AF;"
    warn_c = ";#E4D00A;"
    err__c = ";#DC143C;"
    default_c = ";#5F9EA0;"
    match prefix:
        case "[INFO]":
            color = info_c
        case "[Warn]":
            color = warn_c
        case "[Err ]":
            color = err__c
        case _:
            color = default_c
    cprint(color + prefix, *values, **kwargs)


class _Connect:
    """
    This is a base class,
    which defined some base url for GitHub.
    """
    _BASE_URL = "https://api.github.com/repos/;owner;/;repo;/contents?ref=;branch;"
    _RAW_UEL = "https://raw.githubusercontent.com/;owner;/;repo;/;branch;/;path;"
    _UA = "Mozilla/5.0 " + \
          "(compatible; GiTreeSpider/0.1; " + \
          "+https://github.com/starwindv/gitree)"


class Configer:
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

    def _load(self, force: bool = False):

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


class _GiTree(_Connect):
    def __init__(
            self,
            owner: str,
            repo: str,
            branch: Optional[str] = "main",
            ua: Optional[str] = "",
            timeout: Optional[int | float] = 10.0
    ):
        """
        Args:
            owner (str):
                The owner of the repository to index.
            repo (str):
                The name of the repository to index.
            branch (Optional[str]):
                default: "main"
                The branch of the repository to index.
            ua (Optional[str]):
                default:
                    "Mozilla/5.0 (compatible; GiTreeSpider/0.1; +https://github.com/starwindv/gitree)"
                User agent string for requests.
            timeout (Optional[int|float]):
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
        if ua:
            self._UA = ua
        self._build()
        self.timeout = timeout
        self._initialize()

    def _initialize(self):
        self.data = None
        self.waiting_dir = None
        self.files = None

    def _build(self):
        self._BASE_URL = (
            self._BASE_URL
            .replace(";owner;", self.owner)
            .replace(";repo;", self.repo)
            .replace(";branch;", self.branch)
        )
        self.headers = {
            "User-Agent": self._UA
        }

    def _capture(self, url: str = "") -> json:
        """
        Fetches JSON data from GitHub API endpoint.

        Args:
            url: Target URL to fetch. Uses base URL if empty.

        Returns:
            Parsed JSON response or error dictionary containing:
                "status": "error"
                "type": Exception type name
                "description": Exception description
        """
        try:
            return self.pool.get(
                url if url else self._BASE_URL,
                headers=self.headers,
                timeout=self.timeout
            ).json()
        except Exception as e:
            return {
                "status": "error",
                "type": type(e).__name__,
                "description": repr(e)
            }

    @staticmethod
    def _transform(original_data) -> List[dict]:
        """
        Transforms raw GitHub API response into standardized format.

        Args:
            original_data: Raw response data from GitHub API.

        Returns:
            List of dictionaries with transformed structure containing:
                name: File/directory name.
                path: Full path in repository.
                html_url: GitHub web URL.
                URL: API URL.
                download_url: Raw content URL (files only).
                is_file: Boolean indicating file type.
        """
        transformed = []
        for item in original_data:
            try:
                is_file = item['type'] == 'file'
                transformed_item = {
                    'name': item['name'],
                    'path': item['path'],
                    'html_url': item['html_url'],
                    'url': item['url'],
                    'download_url': item['download_url'],
                    'is_file': is_file
                }
                transformed.append(transformed_item)
            except TypeError:
                cprint(";ff00ff;TypeError")
                print(item)
        return transformed

    def _process(self, url: str = "") -> None:
        """
        Processes API response data and categorizes repository items.

        Args:
            url: URL to process. Uses base URL if empty.

        Notes:
            - Populates two dictionaries:
                files: {path: download_url} for files
                waiting_dir: {path: api_url} for directories
            - Calls _capture and _transform internally
        """
        data = self._capture(url=url)
        self.data = self._transform(data)
        self.waiting_dir = dict()
        self.files = dict()
        for element in self.data:
            is_file = element.get("is_file")
            name = element["path"]
            if is_file:
                self.files.update(
                    {
                        name: element["download_url"]
                    }
                )
                continue
            self.waiting_dir.update(
                {
                    name: element["url"]
                }
            )

    def _loop(self) -> None:
        """
        Performs breadth-first traversal of
        repository directory structure.

        Notes:
            - Processes root directory first
            - Uses queue to handle subdirectories recursively
            - Maintains complete file list in `self.files`
            - Clears waiting_dir after completion
        Returns: None
        """
        if self.data is None:
            self._process()

        # 初始化队列，包含根目录下的所有子目录URL
        queue = list(self.waiting_dir.values())
        # 初始化总文件字典（包含根目录文件）
        all_files = self.files.copy()

        # 广度优先遍历处理所有子目录
        while queue:
            current_url = queue.pop(0)  # 获取队列中的第一个URL
            self._process(url=current_url)  # 处理当前目录

            # 添加当前目录的文件到总字典
            all_files.update(self.files)
            # 将当前目录的子目录加入队列
            queue.extend(self.waiting_dir.values())

        # 更新最终结果
        self.files = all_files
        self.waiting_dir.clear()

    def _download(self, url: str) -> Response:
        """
        Downloads file content from specified URL.

        Args:
            url: Download URL for the file.

        Returns:
            Response object with streaming enabled.
        """
        return self.pool.get(
            url,
            headers=self.headers,
            timeout=self.timeout,
            stream=True
        )

    @staticmethod
    def _thread_download(
            download_func: Callable,
            files: List[tuple],
            total_files: int
    ):
        """
        Manages multithreaded file downloads.
        Args:
            download_func: Download function to execute
            files: List of tuples (path, url) to download
            total_files: Total number of files for progress tracking
        Notes:
            - Uses ThreadPoolExecutor for concurrent downloads
            - Tracks download progress with completion counter
            - Handles and logs exceptions during download
        """
        with ThreadPoolExecutor() as executor:
            # 创建任务列表
            futures = {
                executor.submit(download_func, path, url): (path, url)
                for path, url in files
            }

            # 处理完成的任务
            for i, future in enumerate(as_completed(futures), 1):
                path, url = futures[future]
                try:
                    success = future.result()
                    if success:
                        lprint(f"Downloaded [{i}/{total_files}]: {path}")
                    continue
                except Exception as e:
                    lprint(f"Error processing {path}: {str(e)}", prefix="[Err ]")
                    continue


class GiTree(_GiTree):
    def __init__(
            self,
            *args,
            chunk_size: Optional[int] = 1024,
            save_path: Optional[str] = None,
            when_to_thread: Optional[int] = None,
            **kwargs
    ):
        """
        Args:
            *args                    (Any): Inherited from the parent class `_GiTree`
                owner (str):
                    The owner of the repository to index.
                repo (str):
                    The name of the repository to index.

            chunk_size     (Optional[int]):
                default: `1024`
                The size of the data block used
                when performing streaming downloads and saving.

            save_path      (Optional[str]):
                default: `~/.stv_project/GiTree/repo`
                Download the save path of the obtained file.

            when_to_thread (Optional[int]):
                default: `6`
                When the number of files to be downloaded exceeds this value,
                enable multi-threading downloading.
                If it is less than zero,
                then the program will not use multi-threading to download files.

            **kwargs                 (Any): Inherited from the parent class `_GiTree`
                branch  (Optional[str]):
                    default: "main"
                    The branch of the repository to index.

                ua      (Optional[str]):
                    default:
                        "Mozilla/5.0 (compatible; GiTreeSpider/0.1; +https://github.com/starwindv/gitree)"
                    User agent string for requests.

                timeout (Optional[int|float]):
                    default: 10.0
                    Timeout duration for requests.
        """
        super().__init__(*args, **kwargs)
        self.save_path = None
        # [↑] To defeat IDE's warning, it's so annoying
        # "This feature is defined outside the constructor of the instance"
        if not isinstance(when_to_thread, int):
            raise TypeError(f"The `GiTree.__init__`'s arg `when_to_thread` must be a integer.(got {when_to_thread})")
        self.configer = Configer()
        self.when_to_thread: int = self.configer.parse("when_to_thread") \
            if when_to_thread is None \
            else when_to_thread

        self.chunk_size = chunk_size
        self._initialize_path(save_path)

    def _initialize_path(
            self,
            save_path: str,
    ):
        """
        Initializes and validates repository save path.
        Args:
            save_path (str): The path where to save repository's files

        Raises:
            ValueError, TypeError:
                When the `save_path` is not a valid path,
                raise these errors and prompt relevant information.

        Returns: True|None
            When the save_path was parsed correct:
                return `True`
            else:
                return `None`
        """
        self.save_path = self.configer.parse("save_path") \
            if save_path is None \
            else save_path
        try:
            # 确保基础目录存在
            base_path = os.path.expanduser(self.save_path)
            Path(base_path).mkdir(parents=True, exist_ok=True)

            # 设置完整的保存目录：基础路径 + 仓库名 + 分支名
            self.save_dir = os.path.abspath(
                os.path.join(
                    base_path,
                    self.repo,
                    self.branch
                )
            ).replace("\\", "/")

            # 创建最终保存目录
            Path(self.save_dir).mkdir(parents=True, exist_ok=True)
            return True
        except (ValueError, TypeError) as e:
            raise type(e)(
                f"The `GiTree.initialize`'s arg `path` is not a valid path.(got `{self.save_path}`)"
            ) from e

    def _download_file(self, path: str, url: str) -> bool:
        """
        Downloads and saves a single file.

        Args:
            path (str): Repository relative file path
            url  (str): Download URL for the file

        Returns:
            True if download successful, False otherwise

        Notes:
            - Creates necessary directory structure
            - Uses streaming download with chunked writing
            - Handles HTTP errors and exceptions
        """
        save_to = os.path.join(self.save_dir, path).replace("\\", "/")
        os.makedirs(os.path.dirname(save_to), exist_ok=True)

        try:
            response = self._download(url)
            if response.status_code != 200:
                lprint(f"Failed when download {path} (Status: {response.status_code})", prefix="[Err ]")
                return False

            with open(save_to, 'wb') as f:
                for chunk in response.iter_content(self.chunk_size):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            lprint(f"Error downloading {path}: {str(e)}", prefix="[Err ]")
            return False

    def _thread_download_files(self, files: List[tuple]) -> None:
        """
        Initiates multithreaded download process.

        Args:
            files (List[tuple]): List of tuples (path, url) to download

        Notes:
            - Prints start message with file count
            - Delegates to _thread_download for execution

        """
        total_files = len(files)
        lprint(f"Starting multi-threaded download for {total_files} files...")
        self._thread_download(
            self._download_file,
            files,
            total_files
        )

    def gets(self)->None:
        """
        Main method to retrieve and download repository contents.

        Workflow:
            1. Builds complete file list via _loop
            2. Prints save location and file count
            3. Selects download method based on file count threshold:
               - Sequential download for small file sets
               - Threaded download for large file sets
            4. Prints final success message

        Notes:
            - Download method selection controlled by when_to_thread threshold
        Returns: None
        """
        self._loop()
        lprint(f"Repository files will be saved to: ;ff4433;{self.save_dir}")
        lprint(f"Total files to download: {len(self.files)}")

        files_list = list(self.files.items())
        if len(files_list) < self.when_to_thread:
            lprint("Using sequential download...")
            for i, (path, url) in enumerate(files_list, 1):
                lprint(f"Downloading [{i}/{len(files_list)}]: {path}")
                self._download_file(path, url)
        else:
            self._thread_download_files(files_list)

        lprint(";#228B22;All files downloaded successfully!")