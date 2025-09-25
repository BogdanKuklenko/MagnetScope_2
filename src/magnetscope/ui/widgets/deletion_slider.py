import flet as ft
import time

class DeletionSlider(ft.Control):
    """
    Кастомный виджет-слайдер для подтверждения удаления.
    Принимает в качестве аргумента функцию, которая будет вызвана при успехе.
    """
    def __init__(self, on_delete_confirmed):
        super().__init__()
        # Функция, которая будет вызвана, когда пользователь довел слайдер до конца
        self.on_delete_confirmed = on_delete_confirmed

    def build(self):
        # "Ползунок", который пользователь будет перетаскивать
        self.thumb = ft.Container(
            content=ft.Icon(ft.icons.DELETE_FOREVER, color=ft.Colors.WHITE),
            alignment=ft.alignment.center,
            width=50,
            height=50,
            bgcolor=ft.Colors.RED_600,
            border_radius=ft.border_radius.all(25),
            left=0,
            animate_position=100, # Анимация возврата в исходное положение
        )

        # "Дорожка", по которой движется ползунок
        self.track = ft.Container(
            width=280,
            height=50,
            border_radius=ft.border_radius.all(25),
            bgcolor=ft.Colors.SURFACE_VARIANT,
            content=ft.Row([
                # Подсказка для пользователя
                ft.Text("  Проведите для удаления", color=ft.Colors.ON_SURFACE_VARIANT, italic=True)
            ], alignment=ft.MainAxisAlignment.CENTER),
            animate=100 # Анимация изменения цвета
        )

        # GestureDetector отлавливает жесты перетаскивания
        return ft.GestureDetector(
            on_pan_start=self.drag_start,
            on_pan_update=self.drag_update,
            on_pan_end=self.drag_end,
            content=ft.Stack(
                [
                    self.track,
                    self.thumb,
                ],
                width=280,
                height=50,
            ),
        )

    def drag_start(self, e: ft.DragStartEvent):
        """Вызывается в начале перетаскивания."""
        pass

    def drag_update(self, e: ft.DragUpdateEvent):
        """Вызывается при движении пальца/мыши."""
        max_left = self.track.width - self.thumb.width
        # Рассчитываем новое положение ползунка, не давая ему выйти за пределы дорожки
        new_left = max(0, min(self.thumb.left + e.delta_x, max_left))
        self.thumb.left = new_left

        # Плавно меняем цвет дорожки по мере продвижения
        progress = new_left / max_left
        self.track.bgcolor = ft.Colors.with_opacity(0.5 * progress, ft.Colors.RED_400)
        self.update()

    def drag_end(self, e: ft.DragEndEvent):
        """Вызывается, когда пользователь отпускает палец/мышь."""
        max_left = self.track.width - self.thumb.width
        # Если ползунок доведен почти до конца, считаем действие подтвержденным
        if self.thumb.left >= max_left * 0.9:
            self.thumb.left = max_left
            self.thumb.content.icon = ft.icons.CHECK
            self.thumb.bgcolor = ft.Colors.GREEN_600
            self.update()
            time.sleep(0.3) # Маленькая пауза для визуального фидбэка
            if self.on_delete_confirmed:
                self.on_delete_confirmed() # Вызываем переданную нам функцию
        else:
            # Если нет, плавно возвращаем ползунок в начало
            self.thumb.left = 0
            self.track.bgcolor = ft.Colors.SURFACE_VARIANT
            self.update()
