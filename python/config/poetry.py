from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

import toml


@dataclass
class PoetryConfig:  # pylint: disable=too-many-instance-attributes
    name: str
    version: str
    description: str
    authors: List[str]
    readme: str
    packages: List[Dict[str, str]]
    dependencies: Dict[str, str]
    scripts: Dict[str, str]
    group: Dict[str, Any]

    def add_script(self, name: str, module: str, entry_point: str = "main") -> None:
        self.scripts[name] = f"{module}:{entry_point}"


ConfigPair = Tuple[Dict[str, Any], PoetryConfig]


def load_config(file_name: str) -> ConfigPair:
    with open(file_name, "r", encoding="utf-8") as file:
        config = toml.load(file)

    return config, PoetryConfig(**config["tool"]["poetry"])


def write_config(file_name: str, config_pair: ConfigPair) -> None:
    config, poetry = config_pair
    config["tool"]["poetry"] = poetry.__dict__
    with open(file_name, "w+", encoding="utf-8") as file:
        toml.dump(config, file)
