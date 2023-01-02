import logging

from smb.SMBConnection import SMBConnection

logger = logging.getLogger(__name__)


def connection(pc) -> SMBConnection:
    try:
        conn = SMBConnection(pc.username, pc.pwd, pc.namelocalpc, pc.pcname)
        conn.connect(pc.host, 139)
        return conn
    except Exception:
        logger.warning(f'Fail coonect to host {pc.pcname}, {pc.host}\n\n')
        return False
