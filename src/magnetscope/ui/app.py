import flet as ft
from configparser import ConfigParser
import json
from functools import partial
import random
from urllib.parse import quote
import threading
import time

# Импортируем наши сервисы и виджеты
<<<<<<< HEAD
from data.data_manager import DataManager, INFO_FILENAME, POSTER_FILENAME
=======
from data.data_manager import DataManager, INFO_FILENAME, POSTER_FILENAME, BACKDROP_FILENAME
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
from api.kinopoisk_client import KinopoiskClient
from api.qbittorrent_client import QBittorrentClient
from core.config import save_config
from ui.widgets.deletion_slider import DeletionSlider
from ui.widgets.details_dialog import DetailsDialog # <-- ИМПОРТИРУЕМ НОВЫЙ ДИАЛОГ

class AppUI:
    def __init__(self, page: ft.Page, config: ConfigParser, data_manager: DataManager,
                 kp_client: KinopoiskClient, qbt_client: QBittorrentClient):
        self.page = page; self.config = config; self.data_manager = data_manager; self.kp_client = kp_client; self.qbt_client = qbt_client; self.library_poster_paths = []
        self.search_field = ft.TextField(label="Найти и добавить...", expand=True, on_submit=self.handle_search)
        self.library_grid = ft.GridView(expand=True, runs_count=5, max_extent=180, child_aspect_ratio=0.6, spacing=10, run_spacing=10)
        self.main_content = ft.Container(expand=True, padding=ft.padding.all(10), alignment=ft.alignment.top_center)
        self.navigation_rail = ft.NavigationRail(
            selected_index=0, label_type=ft.NavigationRailLabelType.ALL, min_width=100,
            destinations=[ft.NavigationRailDestination(icon="home_outlined", selected_icon="home", label="Главная"), ft.NavigationRailDestination(icon="movie_outlined", selected_icon="movie", label="Фильмы"), ft.NavigationRailDestination(icon="tv_outlined", selected_icon="tv", label="Сериалы"), ft.NavigationRailDestination(icon="video_library_outlined", selected_icon="video_library", label="Коллекции"), ft.NavigationRailDestination(icon="settings_outlined", selected_icon="settings", label="Настройки")],
            on_change=self.handle_nav_change, group_alignment=-0.9,
        )
        self.kp_token_field = ft.TextField(label="Токен API Кинопоиска", password=True, can_reveal_password=True); self.qbt_host_field = ft.TextField(label="Хост qBittorrent"); self.qbt_port_field = ft.TextField(label="Порт qBittorrent"); self.qbt_user_field = ft.TextField(label="Пользователь qBittorrent"); self.qbt_pass_field = ft.TextField(label="Пароль qBittorrent", password=True, can_reveal_password=True)

        # Глобальный статус-бар загрузки (в AppBar)
        self.current_torrent_hash: str | None = None
        self.global_progress = ft.ProgressBar(value=0, expand=True)
        self.global_percent = ft.Text("0%", size=11)
        self.global_speed = ft.Text("Скорость: 0 КБ/с", size=11)
        self.global_seeds = ft.Text("Сиды: 0", size=11)
        self.global_eta = ft.Text("Осталось: --", size=11)
        self.status_row = ft.Column([
            ft.Row([self.global_progress], expand=True),
            ft.Row([self.global_percent, self.global_speed, self.global_seeds, self.global_eta], spacing=10, alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ], spacing=4)
        self.status_card = ft.Container(
            content=self.status_row,
            bgcolor="surfaceVariant",
            border_radius=ft.border_radius.all(8),
            padding=ft.padding.symmetric(horizontal=10, vertical=6),
            width=360,
            visible=False,
        )
        # Поток мониторинга вместо Timer/Poll (совместимо с вашей версией Flet)
        self._monitor_thread: threading.Thread | None = None
        self._monitor_stop = threading.Event()

    def show_snackbar(self, message: str, color: str = "green"):
        self.page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=color, duration=2000)
        self.page.snack_bar.open = True; self.page.update()

    def handle_show_details(self, movie_data: dict, e):
        """Создает и показывает модальное окно через новый класс."""
        print("--- ШАГ 1: Клик по карточке зарегистрирован! ---")
        dialog = DetailsDialog(self, movie_data)
        self.page.dialog = dialog
        dialog.open = True
        # Доп. страхующий путь через overlay (на случай проблем в конкретной версии Flet)
        try:
            if dialog not in self.page.overlay:
                self.page.overlay.append(dialog)
        except Exception as ex:
            print(f"[Диалог] Не удалось добавить в overlay: {ex}")
        print("--- ШАГ 3: Команда на открытие диалога и обновление страницы отправлена! ---")
        self.page.update()

    def update_movie_data(self, kinopoisk_id: int, new_data: dict):
        """Обновляет JSON-файл для фильма новыми данными."""
        info_path = self.data_manager.get_media_item_path(kinopoisk_id) / INFO_FILENAME
        if info_path.exists():
            with open(info_path, "r+", encoding="utf-8") as f:
                data = json.load(f); data.update(new_data); f.seek(0)
                json.dump(data, f, ensure_ascii=False, indent=4); f.truncate()
    
    def handle_add_movie(self, movie_data: dict, e):
        kinopoisk_id = movie_data.get("id")
        if not kinopoisk_id: return
        if self.data_manager.get_media_item_path(kinopoisk_id).exists(): self.show_snackbar(f"'{movie_data.get('name')}' уже в библиотеке.", "orange"); return
        full_details = self.kp_client.get_movie_details_by_id(kinopoisk_id)
        if not full_details: self.show_snackbar("Не удалось получить детальную информацию.", "red"); return
        self.data_manager.save_media_info(kinopoisk_id, full_details); poster_url = full_details.get("poster", {}).get("url")
        if poster_url: self.data_manager.save_poster(kinopoisk_id, poster_url)
<<<<<<< HEAD
=======
        backdrop = full_details.get("backdrop", {}) if isinstance(full_details.get("backdrop", {}), dict) else {}
        self.data_manager.save_backdrop(
            kinopoisk_id,
            backdrop.get("url"),
            backdrop.get("previewUrl")
        )
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
        self.show_snackbar(f"'{full_details.get('name')}' добавлен в библиотеку!"); self.load_library_items()

    def handle_search(self, e):
        query = self.search_field.value
        if not query: self.load_library_items(); return
        self.library_grid.controls = [ft.Column([ft.ProgressRing(), ft.Text("Идет поиск...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)]; self.page.update(); search_results = self.kp_client.search_movie(query); self.library_grid.controls = []
        if not search_results: self.library_grid.controls.append(ft.Text("Ничего не найдено."))
        else:
            for movie in search_results:
                # Кнопка меню для быстрого поиска на Rutracker
                menu_button = ft.Container(
                    content=ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(text="Добавить в библиотеку", on_click=partial(self.handle_add_movie, movie)),
                            ft.PopupMenuItem(text="Найти на Rutracker", on_click=(lambda e, _title=movie.get('name',''), _year=movie.get('year',''): self.open_rutracker_search(_title, _year))),
                        ]
                    ),
                    right=5,
                    top=5,
                )
                poster = ft.Image(src=movie.get("poster",{}).get("previewUrl", "https://placehold.co/180x270/222/fff?text=No+Image"), border_radius=ft.border_radius.all(8), width=180, height=270, fit=ft.ImageFit.COVER)
                card_content = ft.Stack([poster, menu_button], width=180, height=270)
                clickable_container = ft.Container(content=card_content, on_click=partial(self.handle_add_movie, movie))
                self.library_grid.controls.append(clickable_container)
        self.page.update()
    
    def load_library_items(self):
        self.library_grid.controls = []
        item_paths = sorted([p for p in self.data_manager.media_path.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        self.library_poster_paths = [str((p / POSTER_FILENAME).resolve()) for p in item_paths if (p / POSTER_FILENAME).exists()]
        if not item_paths: self.library_grid.controls.append(ft.Text("Ваша библиотека пуста. Воспользуйтесь поиском."))
        for item_path in item_paths:
            info_file, poster_file = item_path / INFO_FILENAME, item_path / POSTER_FILENAME
            if info_file.exists():
                with open(info_file, "r", encoding="utf-8") as f: data = json.load(f)
                poster_src = str(poster_file.resolve()) if poster_file.exists() else "https://placehold.co/180x270/222/fff?text=No+Poster"
<<<<<<< HEAD
                status_icon = ft.Container()
                if data.get("torrent_hash"): status_icon = ft.Icon(name="download_done", color="green", right=5, top=5)
<<<<<<< HEAD
                card_content = ft.Stack([ft.Column([ft.Image(src=poster_src, border_radius=ft.border_radius.all(8)), ft.Text(data.get('name','N/A'), weight=ft.FontWeight.BOLD, size=14, no_wrap=True), ft.Text(f"{data.get('year', '')}", size=12)], spacing=4, alignment=ft.MainAxisAlignment.START), status_icon])
=======
=======
                status_badge = ft.Container()
                if data.get("torrent_hash"):
                    status_badge = ft.Container(
                        left=10,
                        bottom=10,
                        content=ft.Stack([
                            ft.Container(
                                width=24, 
                                height=24, 
                                bgcolor="black,0.7",
                                border_radius=ft.border_radius.all(12)
                            ),
                            ft.Container(
                                content=ft.Text("q", size=14, weight=ft.FontWeight.BOLD, color="#2C9CFF"),
                                alignment=ft.alignment.center,
                                width=24,
                                height=24
                            ),
                        ]),
                    )
>>>>>>> c7cde51 (Enhance movie card UI with Rutracker search functionality and improve details dialog layout)

                # Меню на карточке: Открыть / Удалить
                kinopoisk_id = data.get("id")
                menu_button = ft.Container(
                    content=ft.PopupMenuButton(
                        items=[
                            ft.PopupMenuItem(text="Открыть", on_click=partial(self.handle_show_details, data)),
                            ft.PopupMenuItem(text="Найти на Rutracker", on_click=(lambda e, _title=data.get('name',''), _year=data.get('year',''): self.open_rutracker_search(_title, _year))),
                            ft.PopupMenuItem(text="Удалить…", on_click=(lambda e, _id=kinopoisk_id, _name=data.get('name',''), _hash=data.get('torrent_hash'): self.open_delete_dialog(_id, _name, _hash))),
                        ]
                    ),
                    right=5,
                    top=5,
                )
<<<<<<< HEAD

                card_main = ft.Column([ft.Image(src=poster_src, border_radius=ft.border_radius.all(8)), ft.Text(data.get('name','N/A'), weight=ft.FontWeight.BOLD, size=14, no_wrap=True), ft.Text(f"{data.get('year', '')}", size=12)], spacing=4, alignment=ft.MainAxisAlignment.START)
                card_content = ft.Stack([card_main, status_icon, menu_button])
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
                clickable_card = ft.Card(ft.Container(content=card_content, on_click=partial(self.handle_show_details, data), border_radius=ft.border_radius.all(8)), elevation=2); self.library_grid.controls.append(clickable_card)
=======
                poster = ft.Image(src=poster_src, border_radius=ft.border_radius.all(8), width=180, height=270, fit=ft.ImageFit.COVER)
                card_content = ft.Stack([poster, status_badge, menu_button], width=180, height=270)
                clickable_container = ft.Container(content=card_content, on_click=partial(self.handle_show_details, data))
                self.library_grid.controls.append(clickable_container)
>>>>>>> c7cde51 (Enhance movie card UI with Rutracker search functionality and improve details dialog layout)
        self.page.update()

    def open_rutracker_search(self, title: str, year: str | int | None):
        query = (title or "").strip()
        if year:
            query = f"{query} {year}".strip()
        if not query:
            return
        self.page.launch_url(f"https://rutracker.org/forum/tracker.php?nm={quote(query)}")
    
    def handle_save_settings(self, e):
        self.config.set("Settings", "kinopoisk_token", self.kp_token_field.value); self.config.set("qBittorrent", "host", self.qbt_host_field.value); self.config.set("qBittorrent", "port", self.qbt_port_field.value); self.config.set("qBittorrent", "user", self.qbt_user_field.value); self.config.set("qBittorrent", "passw", self.qbt_pass_field.value)
        save_config(self.config); self.show_snackbar("Настройки сохранены! Перезапустите приложение.")
    
    def load_settings_to_fields(self):
        self.kp_token_field.value = self.config.get("Settings", "kinopoisk_token"); self.qbt_host_field.value = self.config.get("qBittorrent", "host"); self.qbt_port_field.value = self.config.get("qBittorrent", "port"); self.qbt_user_field.value = self.config.get("qBittorrent", "user"); self.qbt_pass_field.value = self.config.get("qBittorrent", "passw")
    
    def build_settings_view(self) -> ft.Control:
        self.load_settings_to_fields()
        return ft.ListView(controls=[ft.Text("Настройки API", size=20, weight=ft.FontWeight.BOLD), self.kp_token_field, ft.Divider(), ft.Text("Настройки qBittorrent", size=20, weight=ft.FontWeight.BOLD), self.qbt_host_field, self.qbt_port_field, self.qbt_user_field, self.qbt_pass_field, ft.Divider(), ft.ElevatedButton("Сохранить настройки", icon="save", on_click=self.handle_save_settings,), ft.Text("Для применения некоторых настроек требуется перезапуск приложения.", italic=True, color="orange")], spacing=15)

    def navigate_to(self, index: int):
        self.navigation_rail.selected_index = index; self.handle_nav_change(ft.ControlEvent(target=self.navigation_rail, name="change", data=str(index), control=self.navigation_rail, page=self.page))
    
    def build_home_view_panel(self, title: str, section_index: int) -> ft.Control:
        bg_image = random.choice(self.library_poster_paths) if self.library_poster_paths else None
        return ft.Container(content=ft.Stack([ft.Image(src=bg_image, width=1000, height=1000, fit=ft.ImageFit.COVER, opacity=0.2) if bg_image else ft.Container(), ft.Text(title, size=40, weight=ft.FontWeight.BOLD)]), alignment=ft.alignment.center, expand=True, border_radius=ft.border_radius.all(12), border=ft.border.all(2, "surfaceVariant"), on_click=lambda e: self.navigate_to(section_index), ink=True)
    
    def build_home_view(self) -> ft.Control:
        return ft.Row(controls=[self.build_home_view_panel("Фильмы", 1), self.build_home_view_panel("Сериалы", 2), self.build_home_view_panel("Коллекции", 3)], spacing=10, expand=True)
    
    def build_movies_view(self) -> ft.Control:
        search_bar = ft.Row([self.search_field, ft.IconButton(icon="search", on_click=self.handle_search, tooltip="Искать")])
        return ft.Column([ft.Container(content=search_bar, padding=ft.padding.only(bottom=10)), self.library_grid], expand=True)
<<<<<<< HEAD
=======

    def show_person_movies(self, person_id: int, person_name: str):
        """Отображает все фильмы из библиотеки с участием указанного человека."""
        grid = ft.GridView(expand=True, runs_count=5, max_extent=180, child_aspect_ratio=0.6, spacing=10, run_spacing=10)
        item_paths = sorted([p for p in self.data_manager.media_path.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
        count = 0
        for item_path in item_paths:
            info_file, poster_file = item_path / INFO_FILENAME, item_path / POSTER_FILENAME
            if not info_file.exists():
                continue
            with open(info_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            persons = data.get("persons", []) or []
            if any(str(p.get("id")) == str(person_id) for p in persons):
                poster_src = str(poster_file.resolve()) if poster_file.exists() else "https://placehold.co/180x270/222/fff?text=No+Poster"
                status_badge = ft.Container()
                if data.get("torrent_hash"):
                    status_badge = ft.Container(
                        left=10,
                        bottom=10,
                        content=ft.Stack([
                            ft.Container(
                                width=24, 
                                height=24, 
                                bgcolor="black,0.7",
                                border_radius=ft.border_radius.all(12)
                            ),
                            ft.Container(
                                content=ft.Text("q", size=14, weight=ft.FontWeight.BOLD, color="#2C9CFF"),
                                alignment=ft.alignment.center,
                                width=24,
                                height=24
                            ),
                        ]),
                    )
                poster = ft.Image(src=poster_src, border_radius=ft.border_radius.all(8), width=180, height=270, fit=ft.ImageFit.COVER)
                card_content = ft.Stack([poster, status_badge], width=180, height=270)
                clickable_container = ft.Container(content=card_content, on_click=partial(self.handle_show_details, data))
                grid.controls.append(clickable_container)
                count += 1

        header = ft.Row([
            ft.IconButton(icon="arrow_back", tooltip="Назад", on_click=lambda e: (setattr(self.navigation_rail, 'selected_index', 1), self.handle_nav_change(ft.ControlEvent(target=self.navigation_rail, name="change", data="1", control=self.navigation_rail, page=self.page)))),
            ft.Text(f"Фильмы с участием: {person_name}", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True)
        ])

        content = ft.Column([
            ft.Container(content=header, padding=ft.padding.only(bottom=10)),
            grid if count > 0 else ft.Text("В вашей библиотеке нет фильмов с этим участником."),
        ], expand=True)

        self.main_content.content = content
        self.page.update()

    # --- Удаление элемента ---
    def open_delete_dialog(self, kinopoisk_id: int, movie_name: str, torrent_hash: str | None):
        def confirm_delete():
            # Удаляем торрент при необходимости
            if torrent_hash and self.qbt_client and self.qbt_client.is_connected:
                try:
                    self.qbt_client.delete_torrent(torrent_hash, delete_files=True)
                except Exception:
                    pass
            # Удаляем файлы и запись
            self.data_manager.delete_media_item(kinopoisk_id)
            # Закрываем диалог и обновляем список
            dlg.open = False
            self.page.update()
            self.load_library_items()
            self.show_snackbar(f"Удалено: '{movie_name}'", "blue")

        slider = DeletionSlider(on_delete_confirmed=confirm_delete)
        dlg = ft.AlertDialog(modal=True, title=ft.Text(f"Удалить '{movie_name}'?"), content=slider, actions=[ft.TextButton("Отмена", on_click=lambda e: setattr(dlg, 'open', False))])
        self.page.dialog = dlg
        dlg.open = True
        try:
            if dlg not in self.page.overlay:
                self.page.overlay.append(dlg)
        except Exception:
            pass
        self.page.update()
>>>>>>> f107872 (Add initial project structure with core functionality for MagnetScope application)
    
    def handle_nav_change(self, e):
        selected_index = e.control.selected_index
        if selected_index == 0: self.main_content.content = self.build_home_view()
        elif selected_index == 1: self.main_content.content = self.build_movies_view(); self.load_library_items()
        elif selected_index == 2: self.main_content.content = ft.Text("Раздел 'Сериалы' (в разработке)")
        elif selected_index == 3: self.main_content.content = ft.Text("Раздел 'Коллекции' (в разработке)")
        elif selected_index == 4: self.main_content.content = self.build_settings_view()
        self.page.update()

    def build(self):
        self.page.appbar = ft.AppBar(title=ft.Container(), center_title=True, bgcolor="surfaceVariant", actions=[self.status_card])
        self.load_library_items(); self.main_content.content = self.build_home_view()
        layout = ft.Row([self.navigation_rail, ft.VerticalDivider(width=1), self.main_content], expand=True)
        self.page.add(layout); self.page.update()
        # адаптивная ширина карточки статуса
        self.page.on_resized = self._handle_page_resize
        self._handle_page_resize(None)

    # --- Глобальный статус-бар ---
    def start_torrent_monitor(self, torrent_hash: str):
        self.current_torrent_hash = torrent_hash
        self.status_card.visible = True
        self.page.update()
        # Перезапуск фонового мониторинга
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_stop.set(); self._monitor_thread.join(timeout=0.2)
        self._monitor_stop.clear()
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()

    def stop_torrent_monitor(self):
        self.current_torrent_hash = None
        self.status_card.visible = False
        self.global_progress.value = 0
        self.global_percent.value = "0%"
        self.global_speed.value = "0 KB/s"
        self.global_seeds.value = "Сиды: 0"
        self.global_eta.value = "ETA: --"
        self.page.update()

    def _handle_page_resize(self, e):
        try:
            width = int(max(260, min(440, (self.page.window_width or 1000) * 0.32)))
        except Exception:
            width = 360
        self.status_card.width = width
        self.page.update()

    def _monitor_loop(self):
        while not self._monitor_stop.is_set() and self.qbt_client and self.qbt_client.is_connected and self.current_torrent_hash:
            info = self.qbt_client.get_torrent_info(self.current_torrent_hash) or {}
            progress = info.get('progress') or 0
            dlspeed = info.get('dlspeed') or 0
            seeds = info.get('num_seeds') or 0
            eta = info.get('eta') or 0

            def fmt_speed(v: int) -> str:
                kb = 1024; mb = kb*1024; gb = mb*1024
                if v >= gb: return f"{v/gb:.2f} ГБ/с"
                if v >= mb: return f"{v/mb:.2f} МБ/с"
                if v >= kb: return f"{v/kb:.1f} КБ/с"
                return f"{v} Б/с"

            def fmt_eta(sec: int) -> str:
                if not sec or sec < 0: return "--"
                h = sec // 3600; m = (sec % 3600)//60; s = sec % 60
                return f"{h}ч {m}м" if h else (f"{m}м {s}с" if m else f"{s}с")

            def update_ui():
                self.global_progress.value = progress
                self.global_percent.value = f"{progress*100:.1f}%"
                self.global_speed.value = f"Скорость: {fmt_speed(dlspeed)}"
                self.global_seeds.value = f"Сиды: {seeds}"
                self.global_eta.value = f"Осталось: {fmt_eta(eta)}"
                self.page.update()
                if progress >= 0.999:
                    self._monitor_stop.set()
                    self.stop_torrent_monitor()

            try:
                self.page.call_from_thread(update_ui)
            except Exception:
                update_ui()
            time.sleep(1)

    def _on_torrent_tick(self, e):
        if not self.current_torrent_hash or not (self.qbt_client and self.qbt_client.is_connected):
            return
        info = self.qbt_client.get_torrent_info(self.current_torrent_hash)
        if not info:
            return
        progress = info.get('progress') or 0
        dlspeed = info.get('dlspeed') or 0
        seeds = info.get('num_seeds') or 0
        eta = info.get('eta') or 0

        def fmt_speed(v: int) -> str:
            kb = 1024; mb = kb*1024; gb = mb*1024
            if v >= gb: return f"{v/gb:.2f} GB/s"
            if v >= mb: return f"{v/mb:.2f} MB/s"
            if v >= kb: return f"{v/kb:.1f} KB/s"
            return f"{v} B/s"

        def fmt_eta(sec: int) -> str:
            if not sec or sec < 0: return "--"
            h = sec // 3600; m = (sec % 3600)//60; s = sec % 60
            return f"{h}ч {m}м" if h else (f"{m}м {s}с" if m else f"{s}с")

        self.global_progress.value = progress
        self.global_percent.value = f"{progress*100:.1f}%"
        self.global_speed.value = fmt_speed(dlspeed)
        self.global_seeds.value = f"Сиды: {seeds}"
        self.global_eta.value = f"ETA: {fmt_eta(eta)}"
        self.page.update()
        if progress >= 0.999:
            self.stop_torrent_monitor()

