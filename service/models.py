from typing import Any, List, Optional, Union

from pydantic import BaseModel


class RemoteHost(BaseModel):
    """Данные для подключения к удаленному компьютеру."""

    host: str
    pcname: str
    username: str
    pwd: str
    namelocalpc: str


class RemoteDir(BaseModel):
    """Данные об адресе удаленного каталога (диск и расположение каталога на диске)."""

    drive: str
    dir: str


class ActualizeRule(BaseModel):
    """Правила переноса файлов ."""

    source_storage_days: int
    source_delete: bool = False


class TargetData(BaseModel):
    """Савокупная информация о целевом каталоге для резервного копирования данных."""

    target_host: RemoteHost
    target_dir: RemoteDir
    target_limit_count: Optional[int]


class FilesMap(BaseModel):
    """Сведения о месте хранения первичных данных и список каталогов для резервного копирования."""

    source_host: RemoteHost
    source_dir: RemoteDir
    rule: Union[ActualizeRule, Any]
    target: List[TargetData]
