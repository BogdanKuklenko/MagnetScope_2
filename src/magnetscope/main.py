import flet as ft

# Импортируем все наши модули
from core.config import load_config
from data.data_manager import DataManager
from api.kinopoisk_client import KinopoiskClient
from api.qbittorrent_client import QBittorrentClient
from ui.app import AppUI

def main(page: ft.Page):
    """
    Главная функция приложения, точка входа.
    Инициализирует все сервисы и запускает построение UI.
    """
    # 1. Загрузка конфигурации
    config = load_config()

    # 2. Инициализация сервисов на основе конфига
    data_manager = DataManager(config.get("Paths", "data_storage"))
    
    kinopoisk_client = None
    try:
        token = config.get("Settings", "kinopoisk_token")
        kinopoisk_client = KinopoiskClient(token)
    except Exception as e:
        print(f"Ошибка инициализации клиента Кинопоиска: {e}")

    qbt_client = QBittorrentClient(
        host=config.get("qBittorrent", "host"),
        port=config.getint("qBittorrent", "port"),
        user=config.get("qBittorrent", "user"),
        passw=config.get("qBittorrent", "passw")
    )

    # 3. Настройка окна Flet
    page.title = "MagnetScope"
    page.window_width = 1280
    page.window_height = 720
    page.window_min_width = 900
    page.window_min_height = 600
    
    # Устанавливаем тему из конфига
    theme_mode_str = config.get("Settings", "theme", fallback="dark").lower()
    page.theme_mode = ft.ThemeMode.LIGHT if theme_mode_str == "light" else \
                      ft.ThemeMode.SYSTEM if theme_mode_str == "system" else \
                      ft.ThemeMode.DARK
    
    page.padding = 0
    page.clean()

    # 4. Создание и запуск UI
    # Передаем все наши сервисы в класс интерфейса
    app_ui = AppUI(
        page=page,
        config=config,
        data_manager=data_manager,
        kp_client=kinopoisk_client,
        qbt_client=qbt_client
    )

    # Запускаем метод, который будет строить все элементы на странице
    app_ui.build()

    page.update()

if __name__ == "__main__":
    # Запускаем приложение как десктопное приложение (FLET_APP)
    ft.app(target=main, view=ft.AppView.FLET_APP)

