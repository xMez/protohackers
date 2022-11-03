import importlib.resources as pkg_resources
from typing import List


def get_modules(package: str) -> List[str]:
    resources = pkg_resources.contents(package)
    return list(filter(lambda resource: not resource.startswith("__"), resources))


def get_name(module: str) -> str:
    return module[6:]
