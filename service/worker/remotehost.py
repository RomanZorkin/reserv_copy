# В модуле представлены классы для подключения и управления операциями на удаленных ПК
import logging
from typing import List, Optional

from smb import smb_constants as cnst
from smb.base import SharedFile
from smb.SMBConnection import SMBConnection

from service.models import RemoteDir, RemoteHost

logger = logging.getLogger('service')


class HostPC:
    """Класс управляет процессом подключения и взаимодействия с удаленноым компьютером."""

    def __init__(self, hostrules: RemoteHost):
        self.host = hostrules.host
        self.pcname = hostrules.pcname
        self.username = hostrules.username
        self.pwd = hostrules.pwd
        self.namelocalpc = hostrules.namelocalpc

    def connection(self) -> SMBConnection:
        """Метод осуществляет подключение к удаленному компьютеру."""
        try:
            conn = SMBConnection(self.username, self.pwd, self.namelocalpc, self.pcname)
            conn.connect(self.host, 139, timeout=20)
            return conn
        except OSError:
            logger.warning(f'Fail connect to host {self.pcname}, {self.host}\n\n')
            return False

    def remote_map(self, location: RemoteDir) -> List[Optional[SharedFile]]:
        """Метод возвращает список файлов и каталогов на удаленном компьютере."""
        conn = self.connection()
        if not conn:
            return []
        items = conn.listPath(location.drive, location.dir)
        conn.close()
        if not items:
            return []
        return items

    def remote_dirs(self, location: RemoteDir) -> List[Optional[SharedFile]]:
        """Метод возвращает список каталогов на удаленном компьютере."""
        conn = self.connection()
        if not conn:
            return []
        dirs = conn.listPath(
            location.drive,
            location.dir,
            search=cnst.SMB_FILE_ATTRIBUTE_DIRECTORY,
        )
        conn.close()
        if not dirs:
            return []
        return dirs

    def remote_files(self, location: RemoteDir) -> List[Optional[SharedFile]]:
        """Метод возвращает список файлов на удаленном компьютере."""
        conn = self.connection()
        if not conn:
            return []
        files = conn.listPath(
            location.drive,
            location.dir,
            search=cnst.SMB_FILE_ATTRIBUTE_ARCHIVE | cnst.SMB_FILE_ATTRIBUTE_INCL_NORMAL,
            timeout=10,
        )
        conn.close()
        if not files:
            return []
        return files

    def file_exists(self, remote_file: SharedFile, location: RemoteDir) -> SharedFile:
        """Метод проверяет наличие файла на удаленном компьютере."""
        file_path = f'{location.dir}{remote_file.filename}'
        try:
            self.connection().getAttributes(location.drive, file_path)
            self.connection().close()
            return True
        except Exception:
            return False

    def delete_file(self, remote_file: SharedFile, location: RemoteDir) -> bool:
        """Метод удаляет файл на удаленном компьютере."""
        conn = self.connection()
        if not conn:
            return False
        file_path = f'{location.dir}{remote_file.filename}'
        conn.deleteFiles(location.drive, file_path, delete_matching_folders=True)
        conn.close()
        return True
