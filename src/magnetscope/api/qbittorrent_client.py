from qbittorrentapi import Client, LoginFailed, APIConnectionError
from typing import Optional, Dict, Any

class QBittorrentClient:
    """
    Класс-клиент для взаимодействия с Web API qBittorrent.
    """
    def __init__(self, host: str, port: int, user: str, passw: str):
        """
        Инициализирует и настраивает клиент qBittorrent.

        :param host: IP-адрес или доменное имя сервера qBittorrent.
        :param port: Порт Web UI.
        :param user: Имя пользователя.
        :param passw: Пароль.
        """
        self.is_connected = False
        self.client = None

        def try_connect(scheme: str, verify: bool) -> bool:
            try:
                host_arg = host if host.startswith("http") else f"{scheme}://{host}"
                self.client = Client(
                    host=host_arg,
                    port=port,
                    username=user,
                    password=passw,
                    REQUESTS_ARGS={"verify": verify},
                )
                self.client.auth_log_in()
                print(f"Успешное подключение к qBittorrent API через {scheme.upper()} (verify={verify}).")
                return True
            except LoginFailed as e:
                print(f"Ошибка входа в qBittorrent: {e}")
            except APIConnectionError as e:
                print(f"Ошибка подключения к qBittorrent API: {e}")
            except Exception as e:
                print(f"Непредвиденная ошибка при подключении к qBittorrent ({scheme}): {e}")
            return False

        # Пытаемся HTTP, затем HTTPS (с отключенной проверкой сертификата для локального WebUI)
        if try_connect("http", True) or try_connect("http", False) or try_connect("https", False):
            self.is_connected = True

    def add_torrent(self, magnet_link: str, category: str = None) -> Optional[str]:
        """
        Добавляет новый торрент на скачивание по magnet-ссылке.

        :param magnet_link: Magnet-ссылка.
        :param category: Категория для торрента в qBittorrent.
        :return: Хэш торрента в случае успеха, иначе None.
        """
        if not self.is_connected:
            return None
        try:
            result = self.client.torrents_add(urls=magnet_link, category=category)
            if result == "Ok.":
                # Получаем хэш только что добавленного торрента
                torrent_info = self.client.torrents_info(sort="added_on", reverse=True, limit=1)
                if torrent_info:
                    return torrent_info[0].hash
            return None
        except Exception as e:
            print(f"Ошибка добавления торрента: {e}")
            return None

    def get_torrent_info(self, torrent_hash: str) -> Optional[Dict[str, Any]]:
        """
        Возвращает детальную информацию о торренте по его хэшу.

        :param torrent_hash: Хэш торрента.
        :return: Словарь с информацией или None.
        """
        if not self.is_connected:
            return None
        try:
            torrents = self.client.torrents_info(torrent_hashes=torrent_hash)
            if torrents:
                return torrents[0]  # Возвращаем первый и единственный торрент
            return None
        except Exception as e:
            print(f"Ошибка получения информации о торренте {torrent_hash}: {e}")
            return None

    def delete_torrent(self, torrent_hash: str, delete_files: bool = False):
        """
        Удаляет торрент из qBittorrent.

        :param torrent_hash: Хэш торрента.
        :param delete_files: True, если нужно удалить и скачанные файлы.
        """
        if not self.is_connected:
            return
        try:
            self.client.torrents_delete(torrent_hashes=torrent_hash, delete_files=delete_files)
            print(f"Торрент {torrent_hash} успешно удален.")
        except Exception as e:
            print(f"Ошибка удаления торрента {torrent_hash}: {e}")
