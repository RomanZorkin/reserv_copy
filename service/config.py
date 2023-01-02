from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel

from service.models import FilesMap

yaml_file = Path('config.yaml')


class ArchiveRule(BaseModel):
    name: str
    method: int
    filesmap: FilesMap


def load_from_yaml() -> List[ArchiveRule]:
    with open(yaml_file) as fh:
        rule_list = yaml.safe_load(fh)
    return [ArchiveRule(**rule) for rule in rule_list]
