import configparser
from pathlib import Path

# Имя файла конфигурации
CONFIG_FILE = "config.ini"

# Структура конфигурации по умолчанию.
# Пользователь должен будет заменить 'ВАШ_ТОКЕН_ЗДЕСЬ' на свой ключ.
DEFAULT_CONFIG = {
    "Settings": {
        "theme": "dark",
        "kinopoisk_token": "ВАШ_ТОКЕН_ЗДЕСЬ",
    },
    "qBittorrent": {
        "host": "localhost",
        "port": "8080",
        "user": "admin",
        "passw": "adminadmin",
    },
    "Paths": {
        # Путь к основной папке с данными приложения, будет создана рядом с config.ini
        "data_storage": "app_data",
    }
}

def get_config_path() -> Path:
    """Возвращает абсолютный путь к файлу конфигурации."""
    # Мы ожидаем, что файл config.ini будет лежать в корне проекта,
    # рядом с исполняемым файлом или папкой src.
    return Path(CONFIG_FILE).resolve()

def create_default_config(path: Path):
    """Создает файл конфигурации со значениями по умолчанию."""
    config = configparser.ConfigParser()
    config.read_dict(DEFAULT_CONFIG)
    try:
        with open(path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
        print(f"Создан файл конфигурации по умолчанию: {path}")
    except IOError as e:
        print(f"Ошибка при создании файла конфигурации: {e}")


def load_config() -> configparser.ConfigParser:
    """
    Загружает конфигурацию из файла.
    Если файл не существует, создает его со значениями по умолчанию.
    """
    path = get_config_path()
    if not path.exists():
        create_default_config(path)
    
    config = configparser.ConfigParser()
    # Читаем файл с указанием кодировки UTF-8 для поддержки кириллицы
    config.read(path, encoding="utf-8")
    return config

def save_config(config: configparser.ConfigParser):
    """Сохраняет объект конфигурации в файл."""
    path = get_config_path()
    try:
        with open(path, "w", encoding="utf-8") as configfile:
            config.write(configfile)
    except IOError as e:
        print(f"Ошибка при сохранении файла конфигурации: {e}")
