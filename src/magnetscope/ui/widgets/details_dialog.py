import flet as ft
from functools import partial
from typing import TYPE_CHECKING
from urllib.parse import quote

# Импортируем родительский класс и сервисы для подсказок типов
from .deletion_slider import DeletionSlider

if TYPE_CHECKING:
    from ..app import AppUI

class DetailsDialog(ft.AlertDialog):
    """
    Кастомный виджет модального окна с полной информацией о медиа.
    """
    def __init__(self, app_instance: 'AppUI', movie_data: dict):
        super().__init__(modal=True)
        print("--- ШАГ 2: Экземпляр DetailsDialog успешно создается! ---")
        self.app = app_instance
        self.movie_data = movie_data
        
        # Данные из словаря для удобного доступа
        self.kinopoisk_id = self.movie_data.get("id")
        self.torrent_hash = self.movie_data.get("torrent_hash")
        self.movie_title = self.movie_data.get('name', 'Без названия')
        self.year = self.movie_data.get('year', '')

        # Строим UI окна
        self._build_ui()

    def _build_ui(self):
        """Промежуточная версия: заголовок + постер + основные тексты (без торрент-секции и слайдера удаления)."""
        poster_path = self.app.data_manager.get_media_item_path(self.kinopoisk_id) / "poster.jpg"
        poster_src = str(poster_path.resolve()) if poster_path.exists() else "https://placehold.co/300x450/222/fff?text=No+Poster"

        rating = self.movie_data.get('rating', {}).get('kp', 'N/A')
        description = self.movie_data.get('description', 'Нет описания.')
        genres = ", ".join([g['name'] for g in self.movie_data.get('genres', [])[:3]]).capitalize()

        self.title = ft.Text(self.movie_title, size=24, weight=ft.FontWeight.BOLD)
        self.content = ft.Row(
            controls=[
                ft.Image(src=poster_src, height=450, border_radius=ft.border_radius.all(8)),
                ft.Column(
                    controls=[
                        ft.Text(f"Год: {self.year} | Рейтинг KP: {rating}", size=16, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Жанры: {genres}", size=14, italic=True),
                        ft.Divider(),
                        ft.Container(
                            content=ft.Text(description, selectable=True),
                            expand=True,
                            padding=ft.padding.only(top=10, bottom=10)
                        ),
                        ft.Row(
                            controls=[
                                ft.ElevatedButton("Найти на Rutracker", icon="search", on_click=self._handle_find_on_tracker),
                            ],
                            alignment=ft.MainAxisAlignment.SPACE_AROUND
                        )
                    ],
                    expand=True,
                    spacing=10
                )
            ],
            width=800,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        self.actions = [ft.TextButton("Закрыть", on_click=self._close_dialog)]

    def _build_torrent_section(self) -> ft.Control:
        """Строит секцию управления торрентом."""
        if self.torrent_hash and self.app.qbt_client.is_connected:
            torrent_info = self.app.qbt_client.get_torrent_info(self.torrent_hash)
            if torrent_info:
                progress = torrent_info.get('progress', 0)
                state = torrent_info.get('state', 'N/A').capitalize()
                speed = torrent_info.get('dlspeed', 0) / 1024 # KB/s
                
                return ft.Column([
                    ft.Text("Статус загрузки", weight=ft.FontWeight.BOLD),
                    ft.Text(f"Состояние: {state}"),
                    ft.ProgressBar(value=progress),
                    ft.Text(f"{progress*100:.1f}% со скоростью {speed:.1f} KB/s"),
                ])
            else:
                 return ft.Text("Торрент не найден в qBittorrent.")
        else:
            self.magnet_field = ft.TextField(label="Вставьте magnet-ссылку сюда", expand=True)
            return ft.Column([
                ft.Text("Добавить торрент", weight=ft.FontWeight.BOLD),
                ft.Row([
                    self.magnet_field,
                    ft.IconButton(icon="download", tooltip="Скачать", on_click=self._handle_add_torrent)
                ])
            ])

    # --- Обработчики событий ---

    def _close_dialog(self, e=None):
        self.open = False
        self.app.page.update()

    def _handle_add_torrent(self, e=None):
        magnet_link = self.magnet_field.value
        if not magnet_link.startswith("magnet:"):
            self.app.show_snackbar("Некорректная magnet-ссылка.", "red")
            return

        torrent_hash = self.app.qbt_client.add_torrent(magnet_link, category="MagnetScope")
        if torrent_hash:
            self.app.update_movie_data(self.kinopoisk_id, {"torrent_hash": torrent_hash})
            self.app.show_snackbar("Торрент успешно добавлен в qBittorrent!")
            self._close_dialog()
            self.app.load_library_items()
        else:
            self.app.show_snackbar("Не удалось добавить торрент.", "red")

    def _handle_delete_item(self):
        if self.torrent_hash and self.app.qbt_client.is_connected:
            self.app.qbt_client.delete_torrent(self.torrent_hash, delete_files=True)
        
        self.app.data_manager.delete_media_item(self.kinopoisk_id)
        self._close_dialog()
        self.app.load_library_items()
        self.app.show_snackbar("Элемент и связанные файлы удалены.", "blue")

    def _handle_find_on_tracker(self, e=None):
        query = f"{self.movie_title} {self.year}".strip()
        self.app.page.launch_url(f"https://rutracker.org/forum/tracker.php?nm={quote(query)}")
