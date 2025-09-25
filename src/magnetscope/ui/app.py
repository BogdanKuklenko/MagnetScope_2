import flet as ft
from configparser import ConfigParser
import json
from functools import partial
import random

# Импортируем наши сервисы и виджеты
from data.data_manager import DataManager, INFO_FILENAME, POSTER_FILENAME
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
        self.show_snackbar(f"'{full_details.get('name')}' добавлен в библиотеку!"); self.load_library_items()

    def handle_search(self, e):
        query = self.search_field.value
        if not query: self.load_library_items(); return
        self.library_grid.controls = [ft.Column([ft.ProgressRing(), ft.Text("Идет поиск...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER)]; self.page.update(); search_results = self.kp_client.search_movie(query); self.library_grid.controls = []
        if not search_results: self.library_grid.controls.append(ft.Text("Ничего не найдено."))
        else:
            for movie in search_results:
                card_content = ft.Column([ft.Image(src=movie.get("poster",{}).get("previewUrl", "https://placehold.co/180x270/222/fff?text=No+Image"), border_radius=ft.border_radius.all(8)), ft.Text(movie.get('name','N/A'), weight=ft.FontWeight.BOLD, size=14, no_wrap=True), ft.Text(f"{movie.get('year', '')}, {movie.get('type', '')}", size=12)], spacing=4, alignment=ft.MainAxisAlignment.START)
                clickable_card = ft.Card(ft.Container(content=card_content, on_click=partial(self.handle_add_movie, movie), border_radius=ft.border_radius.all(8)), elevation=2); self.library_grid.controls.append(clickable_card)
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
                status_icon = ft.Container()
                if data.get("torrent_hash"): status_icon = ft.Icon(name="download_done", color="green", right=5, top=5)
                card_content = ft.Stack([ft.Column([ft.Image(src=poster_src, border_radius=ft.border_radius.all(8)), ft.Text(data.get('name','N/A'), weight=ft.FontWeight.BOLD, size=14, no_wrap=True), ft.Text(f"{data.get('year', '')}", size=12)], spacing=4, alignment=ft.MainAxisAlignment.START), status_icon])
                clickable_card = ft.Card(ft.Container(content=card_content, on_click=partial(self.handle_show_details, data), border_radius=ft.border_radius.all(8)), elevation=2); self.library_grid.controls.append(clickable_card)
        self.page.update()
    
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
    
    def handle_nav_change(self, e):
        selected_index = e.control.selected_index
        if selected_index == 0: self.main_content.content = self.build_home_view()
        elif selected_index == 1: self.main_content.content = self.build_movies_view(); self.load_library_items()
        elif selected_index == 2: self.main_content.content = ft.Text("Раздел 'Сериалы' (в разработке)")
        elif selected_index == 3: self.main_content.content = ft.Text("Раздел 'Коллекции' (в разработке)")
        elif selected_index == 4: self.main_content.content = self.build_settings_view()
        self.page.update()

    def build(self):
        self.page.appbar = ft.AppBar(title=ft.Text("MagnetScope"), center_title=True, bgcolor="surfaceVariant")
        self.load_library_items(); self.main_content.content = self.build_home_view()
        layout = ft.Row([self.navigation_rail, ft.VerticalDivider(width=1), self.main_content], expand=True)
        self.page.add(layout); self.page.update()

