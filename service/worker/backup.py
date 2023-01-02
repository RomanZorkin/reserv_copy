from typing import List

from service.config import ArchiveRule
from service.worker.archive import Actualize


def run(rule_list: List[ArchiveRule]):
    for rule in rule_list:
        if rule.method == 1:
            Actualize(rule.filesmap).run()
