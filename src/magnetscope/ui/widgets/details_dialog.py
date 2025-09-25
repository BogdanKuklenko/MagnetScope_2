import flet as ft
from functools import partial
<<<<<<< HEAD
from typing import TYPE_CHECKING
=======
from typing import TYPE_CHECKING, List, Dict, Any
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
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
<<<<<<< HEAD
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
=======
        """Полная версия UI модального окна со всеми секциями."""
        item_dir = self.app.data_manager.get_media_item_path(self.kinopoisk_id)
        poster_path = item_dir / "poster.jpg"
        poster_src = str(poster_path.resolve()) if poster_path.exists() else "https://placehold.co/300x450/222/fff?text=No+Poster"

        backdrop_path = item_dir / "backdrop.jpg"
        backdrop_src = str(backdrop_path.resolve()) if backdrop_path.exists() else None

        rating = self.movie_data.get('rating', {}).get('kp', 'N/A')
        description = self.movie_data.get('description') or "Нет описания."
        genres_list = [g.get('name') for g in (self.movie_data.get('genres') or [])]
        genres = ", ".join(genres_list[:6]).capitalize() if genres_list else ""

        # Внешние ссылки
        imdb_id = (self.movie_data.get('externalId') or {}).get('imdb')
        kp_id = self.kinopoisk_id
        links_row = ft.Row([
            ft.IconButton(icon="link", tooltip="Открыть на Кинопоиске", on_click=lambda e: self.app.page.launch_url(f"https://www.kinopoisk.ru/film/{kp_id}/")),
            ft.IconButton(icon="movie", tooltip="Открыть на IMDb", on_click=(lambda e: self.app.page.launch_url(f"https://www.imdb.com/title/{imdb_id}/")) if imdb_id else None, disabled=not bool(imdb_id)),
        ], spacing=10)

        # Участники: режиссер и актёры
        persons: List[Dict[str, Any]] = self.movie_data.get('persons') or []
        director = next((p for p in persons if (p.get('enProfession') == 'director' or p.get('profession') == 'режиссеры')), None)
        actors = [p for p in persons if (p.get('enProfession') == 'actor' or p.get('profession') == 'актеры')]
        main_actors = actors[:10]

        def person_chip(p):
            name = p.get('name') or p.get('enName') or 'Без имени'
            pid = p.get('id')
            return ft.Chip(label=ft.Text(name, selectable=False), on_click=lambda e, _pid=pid, _name=name: self.app.show_person_movies(_pid, _name))

        director_row = ft.Row([ft.Text("Режиссёр:", weight=ft.FontWeight.BOLD)] + ([person_chip(director)] if director else []), wrap=True)
        actors_row = ft.Row([ft.Text("Актёры:", weight=ft.FontWeight.BOLD)] + [person_chip(a) for a in main_actors], wrap=True)

        # Секция торрент
        torrent_section = self._build_torrent_section()

        # Добавление в коллекции
        existing_collections = self.app.data_manager.get_collection_names()
        self.collection_dropdown = ft.Dropdown(options=[ft.dropdown.Option(c) for c in existing_collections], hint_text="Добавить в коллекцию", width=260)
        self.collection_field_new = ft.TextField(label="Новая коллекция", width=200)
        add_to_collection_row = ft.Row([
            self.collection_dropdown,
            self.collection_field_new,
            ft.ElevatedButton("Добавить", icon="add", on_click=self._handle_add_to_collection)
        ], spacing=8)

        # Слайдер удаления
        delete_slider = DeletionSlider(on_delete_confirmed=self._handle_delete_item)

        # Контент справа со скроллом всей колонки
        right_controls = [
            ft.Text(f"Год: {self.year} | Рейтинг KP: {rating}", size=16, weight=ft.FontWeight.BOLD),
            ft.Text(f"Жанры: {genres}", size=14, italic=True),
            links_row,
            ft.Divider(),
            director_row,
            actors_row,
            ft.Divider(),
            ft.Container(
                content=ft.ListView(
                    controls=[ft.Text(description, selectable=True)],
                    expand=True
                ),
                expand=True,
                height=200,
                border=ft.border.all(1, "surfaceVariant"),
                padding=ft.padding.all(10),
                border_radius=ft.border_radius.all(6),
            ),
            ft.Divider(),
            torrent_section,
            ft.Divider(),
            add_to_collection_row,
            ft.Divider(),
            delete_slider,
        ]
        right_column = ft.Container(content=ft.ListView(controls=right_controls, expand=True, spacing=10), expand=True)

        # Кинематографичный фон
        background = ft.Image(src=backdrop_src, fit=ft.ImageFit.COVER, opacity=0.15) if backdrop_src else ft.Container()

        body = ft.Stack([
            background,
            ft.Container(
                content=ft.Row([
                    ft.Stack([
                        ft.Image(src=poster_src, height=450, border_radius=ft.border_radius.all(8)),
                        ft.Container(left=10, bottom=10, content=ft.Stack([
                            ft.Container(width=16, height=16, bgcolor="black", opacity=0.22, border_radius=ft.border_radius.all(5)),
                            ft.Container(content=ft.Text("q", size=11, weight=ft.FontWeight.BOLD, color="#2C9CFF"), alignment=ft.alignment.center),
                        ], width=16, height=16)),
                    ]),
                    right_column
                ], width=900, vertical_alignment=ft.CrossAxisAlignment.START, expand=False),
                padding=ft.padding.all(16),
                width=920,
            )
        ], width=940, height=520)

        self.title = ft.Text(self.movie_title, size=24, weight=ft.FontWeight.BOLD)
        self.content = body
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
        self.actions = [ft.TextButton("Закрыть", on_click=self._close_dialog)]

    def _build_torrent_section(self) -> ft.Control:
        """Строит секцию управления торрентом."""
        def build_magnet_input(notice: str | None = None) -> ft.Control:
            # Поле ввода плюс управление персональной сохраненной ссылкой для текущего фильма
            saved_for_item = self.app.data_manager.get_saved_magnet_for_item(self.kinopoisk_id) or ""
            self.magnet_field = ft.TextField(label="Вставьте magnet-ссылку сюда", expand=True, value=saved_for_item)
            actions_row = ft.Row([
                ft.IconButton(icon="download", tooltip="Скачать", on_click=self._handle_add_torrent),
                ft.IconButton(icon="content_copy", tooltip="Копировать", on_click=lambda e: (self.app.page.set_clipboard(self.magnet_field.value), self.app.show_snackbar("Ссылка скопирована"))),
                ft.IconButton(icon="save", tooltip="Сохранить", on_click=lambda e: (self.app.data_manager.set_saved_magnet_for_item(self.kinopoisk_id, self.magnet_field.value), self.app.show_snackbar("Ссылка сохранена"))),
                ft.IconButton(icon="delete", tooltip="Удалить", on_click=lambda e: (self.app.data_manager.set_saved_magnet_for_item(self.kinopoisk_id, None), setattr(self.magnet_field, 'value', ''), self.app.show_snackbar("Ссылка удалена"), self.app.page.update())),
                ft.ElevatedButton("Найти на Rutracker", icon="search", on_click=lambda e: self.app.open_rutracker_search(self.movie_title, self.year)),
            ], spacing=6)
            items: list[ft.Control] = [
                ft.Text("Торренты", weight=ft.FontWeight.BOLD),
                self.magnet_field,
                actions_row,
            ]
            if notice:
                items.insert(1, ft.Text(notice, color="orange"))
            return ft.Column(items, spacing=8)

        if self.app.qbt_client.is_connected:
            if self.torrent_hash:
                torrent_info = self.app.qbt_client.get_torrent_info(self.torrent_hash)
                if torrent_info:
                    # Индикатор перенесён в AppBar — покажем уведомление И блок работы с ссылкой
                    notice = ft.Row([
                        ft.Icon(name="info"),
                        ft.Text("Загрузка отображается вверху рядом с названием программы", italic=True, color="onSurfaceVariant"),
                    ], spacing=8)
                    return ft.Column([
                        notice,
                        build_magnet_input(),
                    ], spacing=8)
                else:
                    return build_magnet_input("Торрент не найден в qBittorrent.")
            # нет torrent_hash
            return build_magnet_input()
        else:
            return build_magnet_input("qBittorrent не подключен. Проверьте настройки.")

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
            self.app.data_manager.save_magnet_link(magnet_link)
            self.app.data_manager.set_saved_magnet_for_item(self.kinopoisk_id, magnet_link)
            # Запускаем глобальный мониторинг прогресса
            self.app.start_torrent_monitor(torrent_hash)
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
<<<<<<< HEAD
=======

    def _handle_add_to_collection(self, e=None):
        new_collection_name = (self.collection_field_new.value or "").strip()
        selected_collection = (self.collection_dropdown.value or "").strip()
        target_collection = new_collection_name or selected_collection
        if not target_collection:
            self.app.show_snackbar("Укажите или выберите коллекцию.", "orange")
            return
        ok = self.app.data_manager.add_to_collection(self.kinopoisk_id, target_collection)
        if ok:
            self.app.show_snackbar(f"Добавлено в коллекцию: {target_collection}")
            # Обновим список коллекций в дропдауне
            self.collection_dropdown.options = [ft.dropdown.Option(c) for c in self.app.data_manager.get_collection_names()]
            self.collection_dropdown.value = target_collection
            self.collection_field_new.value = ""
            self.app.page.update()
        else:
            self.app.show_snackbar("Не удалось добавить в коллекцию.", "red")
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
