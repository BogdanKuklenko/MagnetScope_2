import requests
import time
import random
from typing import Optional, Dict, Any, List, Union

# Базовый URL для API Кинопоиска (v1.4)
API_BASE_URL = "https://api.kinopoisk.dev/v1.4"

class KinopoiskClient:
    """
    Класс для взаимодействия с неофициальным API Кинопоиска.
    """
    def __init__(self, token: str):
        """
        Инициализирует клиент.

        :param token: API-ключ (токен) для доступа к API.
        """
        if not token or token == "ВАШ_ТОКЕН_ЗДЕСЬ":
            raise ValueError("Токен для API Кинопоиска не указан в config.ini")
            
        self.headers = {
            "accept": "application/json",
            "X-API-KEY": token
        }
        # Reasonable default timeouts: (connect, read)
        self._timeout = (5, 20)
        # Используем сессию для переиспользования соединений и явного контроля прокси
        self._session = requests.Session()
        # По умолчанию игнорируем системные переменные прокси во избежание ложной маршрутизации
        self._session.trust_env = False

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Выполняет GET-запрос к API и возвращает JSON-ответ.

        :param endpoint: Конечная точка API (например, 'movie/search').
        :param params: Параметры запроса.
        :return: Ответ в формате dict или None в случае ошибки.
        """
        url = f"{API_BASE_URL}/{endpoint}"
        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                response = self._session.get(url, headers=self.headers, params=params, timeout=self._timeout)
                # Повторяем при 429 и 5xx кодах
                if response.status_code in (429,) or 500 <= response.status_code < 600:
                    raise requests.HTTPError(f"HTTP {response.status_code}")
                response.raise_for_status()
                return response.json()
            except (requests.Timeout, requests.ConnectionError, requests.HTTPError) as e:
                if attempt == max_attempts:
                    print(f"Ошибка запроса к API Кинопоиска ({url}) после {attempt} попыток: {e}")
                    return None
                # Экспоненциальная задержка с джиттером
                backoff_sec = (2 ** (attempt - 1)) + random.uniform(0, 0.5)
                time.sleep(backoff_sec)
            except requests.RequestException as e:
                print(f"Ошибка запроса к API Кинопоиска ({url}): {e}")
                return None

    def search_movie(self, query: str, limit: int = 5, media_type: Optional[str] = None, year: Optional[int] = None, page: int = 1) -> List[Dict[str, Any]]:
        """
        Выполняет поиск медиа по названию.

        :param query: Поисковый запрос (название фильма/сериала).
        :param limit: Количество результатов для возврата.
        :param media_type: Тип медиа (например, "movie" или "tv-series").
        :param year: Год выхода.
        :param page: Номер страницы.
        :return: Список найденных медиа в виде словарей.
        """
        params: Dict[str, Any] = {"page": page, "limit": limit, "query": query}
        if media_type:
            params["type"] = media_type
        if year:
            params["year"] = year
        result = self._make_request("movie/search", params=params)
        return result.get("docs", []) if result else []

    def get_movie_details_by_id(self, kinopoisk_id: Union[int, str]) -> Optional[Dict[str, Any]]:
        """
        Получает полную информацию о медиа по его ID на Кинопоиске.

        :param kinopoisk_id: ID фильма/сериала.
        :return: Словарь с детальной информацией или None.
        """
        return self._make_request(f"movie/{kinopoisk_id}")
