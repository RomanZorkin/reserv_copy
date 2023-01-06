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

    def __init__(self, navigator: FilesMap):
        """Init Actualize class.

        Arguments:
            navigator (FilesMap): набор правил архивации.
        """
        self.source_host = HostPC(navigator.source_host)
        self.source_conn = self.source_host.connection
        self.source_dir = navigator.source_dir
        self.rule = navigator.rule
        self.target_list: List[TargetData] = navigator.target

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

    def delete_old_file(
        self, source_file: SharedFile, source_dir: RemoteDir, del_tag: bool,
    ) -> bool:
        """Метод удаляет файл на удаленном компьютере при необходимости.

        Arguments:
            source_file (SharedFile): файл для удаления.
            source_dir (RemoteDir): местонахождение файла.
            del_tag (bool): признак необходиомти удаления файла.

        Returns:
            bool:  True если файл удален успешно.
        """
        if not del_tag:
            return True
        logger.debug(f'delete file {source_file.filename} {source_dir}')
        return self.source_host.delete_file(source_file, source_dir)

    def garbage_clean(self) -> bool:
        """."""
        for target in self.target_list:
            target_host = HostPC(target.target_host)
            archive_files = target_host.remote_files(target.target_dir)
            if not archive_files:
                return False
            garbage_files = self._get_garbage_files(target, archive_files)
            if not garbage_files:
                return False
            for old_file in garbage_files:
                if not self.delete_old_file(old_file, target.target_dir, del_tag=True):
                    return False
        return True

    def _get_garbage_files(
        self, target_rule: TargetData, archive_files: List[SharedFile],
    ) -> List[SharedFile]:
        """Метод формирует список файлов подлежащих удалению в заданной дирректории.

        Arguments:
            target_rule (TargetData): набор правил для удаленной дирректории с архивными файлами,
                нам необходим target_rule.target_limit_count, который устанавливает минимальное
                количество файлов, которые должны остаться в дирректории.
            archive_files (List[SharedFile]): список файлов, находящихся в заданной директории,
                которые проверяются на необходимость удаления.
        """
        if not target_rule.target_limit_count:
            return []
        files_dict = {}
        for archive_file in archive_files:
            files_dict[archive_file] = datetime.fromtimestamp(archive_file.last_write_time)
        garbage_dict = {
            file: file_date for file, file_date in sorted(
                files_dict.items(), key=lambda item: item[1],
            )
        }
        old_items = len(list(garbage_dict)) - target_rule.target_limit_count
        if old_items < 0:
            return []
        return list(garbage_dict)[:old_items]


class Actualize(Archivator):
    """Класс содержит правила по переносу файлов в зависимости от даты создания.

    Attributes:
        source_host (HostPC): настройки удаленного компьютера, откуда копируются файлы.
        source_conn (SMBConnection): метод устанавливает соеденияние с удаленным компьютером.
        source_dir (RemoteDir): сведения о пути до дирректории откуда копируются файлы.
        target_list (List[TargetData]): перечень удаленных компьютеров и дирректорий куда \
            архивируются файлы.
    """

    def __init__(self, navigator: FilesMap):
        """Init Actualize class.

        Arguments:
            navigator (FilesMap): набор правил архивации.
        """
        super().__init__(navigator)

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

    def search_old_source(self, source_file: SharedFile) -> bool:
        """Метод запускает процесс архивации если файл соответствует правилу времени.

        В теле метода запускается цикл для каждого целевого каталога архивирования.

        Arguments:
            source_file (SharedFile): файл для архивации.

        Returns:
            bool:  True если файл архиврован успешно.
        """
        if self.period_control(source_file, self.rule.source_storage_days):
            copy_errors = []
            for target in self.target_list:
                if not self.copy_file(source_file, HostPC(target.target_host), target.target_dir):
                    copy_errors.append(True)
            if not copy_errors:
                return self.delete_old_file(source_file, self.source_dir, self.rule.source_delete)
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
                logger.debug(message)
        logger.debug('operation complete')
        self.garbage_clean()
        return True


class Overwrite(Archivator):
    """Класс содержит правила по перезаписи существующих файлов на актуальные."""

    pass
