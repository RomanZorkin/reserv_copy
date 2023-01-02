import logging
import tempfile
from datetime import datetime, timedelta
from typing import List

from smb.base import SharedFile

from service.models import FilesMap, RemoteDir, TargetData
from service.worker.remotehost import HostPC

logger = logging.getLogger(__name__)


class Archivator:
    """Класс отвечает за управление процессом архивации файлов."""

    def period_control(self, target_file: SharedFile, rule: int) -> bool:
        """Метод сравнивает дату файла и теущую дату.

        Возвращает True если дата файла меньше текущей даты на заданное rule количество дней.
        Если задать rule отрицательным, тогда True если дата файла больше текущей даты на rule.
        При rule = 0 месяца одинаковые.
        """
        file_date = datetime.fromtimestamp(target_file.last_write_time)
        control_date = datetime.now() - timedelta(days=rule)
        if rule != 0:
            if control_date >= file_date:
                return True
            else:
                return False  # noqa:WPS503 условие применяется для rule != 0
        if control_date.month == file_date.month:
            return True
        return False


class Actualize(Archivator):
    """Класс содержит правила по переносу файлов в зависимости от даты создания.

    Atributes:
        source_host (HostPC): настройки удаленного компьютера, откуда копируются файлы.
        source_conn (SMBConnection): метод устанавливает соеденияние с удаленным компьютером.
        source_dir (RemoteDir): сведения о пути до дирректории откуда копируются файлы.
        target_list (List[TargetData]): перечень удаленных компьютеров и дирректорий куда \
            архивируются файлы.
    """

    def __init__(self, navigator: FilesMap):
        """Init Actualize class.

        Args:
            navigator (FilesMap): набор правил архивации.
        """
        self.source_host = HostPC(navigator.source_host)
        self.source_conn = self.source_host.connection
        self.source_dir = navigator.source_dir
        self.rule = navigator.rule
        self.target_list: List[TargetData] = navigator.target

    def copy_file(
        self, source_file: SharedFile, target_host: HostPC, target_dir: RemoteDir,
    ) -> bool:
        """Метод копирует файл из источника в целевой каталог.

        Arguments:
            source_file (SharedFile): файл для копирования.
            target_host (HostPC): настройки подключения к удаленному компьютеру.
            target_dir (RemoteDir): расположения каталога куда копируются файлы.

        Returns:
            bool:  True если файл скопирован успешно.
        """
        source_path = '{0}{1}'.format(self.source_dir.dir, source_file.filename)
        target_path = '{0}{1}'.format(target_dir.dir, source_file.filename)
        if target_host.file_exists(source_file, target_dir):
            return True
        try:
            with tempfile.NamedTemporaryFile() as tmp:
                # Подключение к удаленному компьютеру получение файл_объект метод read
                self.source_conn().retrieveFile(self.source_dir.drive, source_path, tmp)
                # Переход в начало файл_объект
                tmp.seek(0)
                # Подключению к удаленному компьютеру запись файл_объекта в файл метод write
                target_host.connection().storeFileFromOffset(target_dir.drive, target_path, tmp)
            self.source_conn().close()
            if target_host.file_exists(source_file, target_dir):
                target_host.connection().close()
                return True
            return False
        except Exception:
            self.source_conn().close()
            target_host.connection().close()
            return False

    def delete_old_file(self, source_file: SharedFile) -> bool:
        """Метод удаляет архивируемый файл при необходимости."""
        if not self.rule.source_delete:
            return True
        return self.source_host.delete_file(source_file, self.source_dir)

    def search_old_source(self, source_file: SharedFile) -> bool:
        if self.period_control(source_file, self.rule.source_storage_days):
            copy_errors = []
            for target in self.target_list:
                if not self.copy_file(source_file, HostPC(target.target_host), target.target_dir):
                    copy_errors.append(True)
            if not copy_errors:
                return self.delete_old_file(source_file)
            return False
        return False

    def run(self) -> bool:
        logger.debug('start run fun')
        files = self.source_host.remote_files(self.source_dir)
        logger.debug(f'Get files {files}')
        if not files:
            return False
        for file in files:
            if not file:
                continue
            result = self.search_old_source(file)
            if not result:
                message = """
Файл {0} не обработан. Возраст файла не менее {1} дней, подлежит удалению \
в исходном каталоге - {2}""".format(
                    file.filename, self.rule.source_storage_days, self.rule.source_delete,
                )
                print(message)
        return True


class Overwrite(Archivator):
    """Класс содержит правила по перезаписи существующих файлов на актуальные."""

    pass
