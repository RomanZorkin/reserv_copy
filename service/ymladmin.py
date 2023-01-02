from pathlib import Path
from typing import Any, Dict, List

import yaml

config = Path('config.yaml')


rule = [
    {
        'name': '1C_enterprize_actualize',
        'method': 1,
        'filesmap': {
            'source_host': {
                'host': '192.168.0.1',
                'pcname': 'server',
                'username': 'admin',
                'pwd': '1111',
                'namelocalpc': 'pm11',
            },
            'source_dir': {
                'drive': 'i',
                'dir': '/1C Предприятие/Бухгалтерия/Архивы/Текущая архивация/',
            },
            'rule': {
                'source_storage_days': -1,
                'source_delete': False,
            },
            'target': [
                {
                    'target_host': {
                        'host': '192.168.0.1',
                        'pcname': 'server',
                        'username': 'admin',
                        'pwd': '1111',
                        'namelocalpc': 'pm11',
                    },
                    'target_dir': {
                        'drive': 'f',
                        'dir': '/data_base/1C_Enterprize/1_enterprise/archives/',
                    },
                },
            ],
        },
    },
    {
        'name': '1C_enterprize_actualize',
        'method': 1,
        'filesmap': {
            'source_host': {
                'host': '192.168.0.1',
                'pcname': 'server',
                'username': 'admin',
                'pwd': '1111',
                'namelocalpc': 'pm11',
            },
            'source_dir': {
                'drive': 'i',
                'dir': '/1C Предприятие/Бухгалтерия/Архивы/Текущая архивация/',
            },
            'rule': {
                'source_storage_days': 31,
                'source_delete': True,
            },
            'target': [
                {
                    'target_host': {
                        'host': '192.168.0.1',
                        'pcname': 'server',
                        'username': 'admin',
                        'pwd': '1111',
                        'namelocalpc': 'pm11',
                    },
                    'target_dir': {
                        'drive': 'h',
                        'dir': '/Архив 1с/Бухгалтерия/2022/',
                    },
                },
            ],
        },
    },
]


def write_config(config_rule: List[Dict[str, Any]], config_path: Path) -> None:
    with open(config, 'w') as file:
        yaml.dump(config_rule, file, default_flow_style=False)


write_config(rule, config)
