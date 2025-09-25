import json
import shutil
from pathlib import Path
import requests
from typing import Union, Dict, Any, Optional
import time
import random

# Имена файлов для стандартных данных
INFO_FILENAME = "info.json"
POSTER_FILENAME = "poster.jpg"
BACKDROP_FILENAME = "backdrop.jpg"
HISTORY_FILENAME = "download_history.json"


class DataManager:
    """
    Управляет всеми данными приложения: создает папки, сохраняет метаданные,
    постеры и управляет историей загрузок.
    """

    def __init__(self, base_data_path: str):
        """
        Инициализирует менеджер данных.

        :param base_data_path: Путь к корневой папке для хранения данных.
        """
        self.base_path = Path(base_data_path).resolve()
        self.media_path = self.base_path / "media_data"
        self.history_path = self.base_path / HISTORY_FILENAME

        # Создаем необходимые директории, если их нет
        self.base_path.mkdir(exist_ok=True)
        self.media_path.mkdir(exist_ok=True)

    def get_media_item_path(self, kinopoisk_id: Union[int, str]) -> Path:
        """Возвращает путь к папке конкретного фильма/сериала."""
        return self.media_path / str(kinopoisk_id)

    def save_media_info(self, kinopoisk_id: Union[int, str], data: Dict[str, Any]):
        """Сохраняет текстовую информацию о медиа (info.json)."""
        item_path = self.get_media_item_path(kinopoisk_id)
        item_path.mkdir(exist_ok=True)
        info_file_path = item_path / INFO_FILENAME

        try:
            with open(info_file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения {INFO_FILENAME} для id {kinopoisk_id}: {e}")

    def save_poster(self, kinopoisk_id: Union[int, str], poster_url: str, fallback_url: Optional[str] = None):
        """Скачивает и сохраняет постер медиа."""
        item_path = self.get_media_item_path(kinopoisk_id)
        item_path.mkdir(exist_ok=True)
        poster_file_path = item_path / POSTER_FILENAME

        # Сессия без системных прокси
        session = requests.Session()
        session.trust_env = False
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Accept-Language": "ru,en;q=0.9",
        }

        def try_download(url: str) -> bool:
            if not url:
                return False
            max_attempts = 3
            for attempt in range(1, max_attempts + 1):
                try:
                    # Сначала обычная проверка сертификата
                    resp = session.get(url, headers=headers, stream=True, timeout=(5, 20))
                    if resp.status_code in (429,) or 500 <= resp.status_code < 600:
                        raise requests.HTTPError(f"HTTP {resp.status_code}")
                    resp.raise_for_status()
                    content_type = resp.headers.get("Content-Type", "")
                    if "image" not in content_type:
                        raise requests.RequestException(f"Unexpected content-type: {content_type}")
                    with open(poster_file_path, "wb") as f:
                        for chunk in resp.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                    return True
                except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                    if attempt == max_attempts:
                        # Попробуем повтор с verify=False на последней неудаче
                        try:
                            resp = session.get(url, headers=headers, stream=True, timeout=(5, 20), verify=False)
                            resp.raise_for_status()
                            content_type = resp.headers.get("Content-Type", "")
                            if "image" not in content_type:
                                raise requests.RequestException(f"Unexpected content-type: {content_type}")
                            with open(poster_file_path, "wb") as f:
                                for chunk in resp.iter_content(chunk_size=8192):
                                    if chunk:
                                        f.write(chunk)
                            return True
                        except Exception:
                            print(f"Ошибка скачивания постера (после {attempt} попыток) для id {kinopoisk_id}: {e}")
                            return False
                    else:
                        backoff = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                        time.sleep(backoff)
                except requests.RequestException as e:
                    print(f"Ошибка скачивания постера для id {kinopoisk_id}: {e}")
                    return False
            return False

        # Сначала пробуем основной URL, потом запасной
        if try_download(poster_url):
            return
        if fallback_url and try_download(fallback_url):
            return
        print(f"Не удалось сохранить постер для id {kinopoisk_id} по доступным URL.")

    def delete_media_item(self, kinopoisk_id: Union[int, str]):
        """Удаляет папку со всеми данными о медиа."""
        item_path = self.get_media_item_path(kinopoisk_id)
        if item_path.exists() and item_path.is_dir():
            try:
                shutil.rmtree(item_path)
            except OSError as e:
                print(f"Ошибка удаления папки {item_path}: {e}")

    def load_download_history(self) -> Dict[str, Any]:
        """Загружает историю загрузок из JSON-файла."""
        if not self.history_path.exists():
            return {}
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (IOError, json.JSONDecodeError) as e:
            print(f"Ошибка загрузки истории: {e}")
            return {}

    def save_download_history(self, history_data: Dict[str, Any]):
        """Сохраняет историю загрузок в JSON-файл."""
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Ошибка сохранения истории: {e}")
