import flet as ft
import time


def DeletionSlider(on_delete_confirmed):
    """Фабричная функция: возвращает GestureDetector с дорожкой и ползунком.

    Совместимо с вашей версией Flet: используем строковые имена и цвета,
    без ft.icons / ft.Colors / UserControl.
    """
    thumb = ft.Container(
        content=ft.Icon(name="delete_forever", color="white"),
        alignment=ft.alignment.center,
        width=50,
        height=50,
        bgcolor="red",
        border_radius=ft.border_radius.all(25),
        left=0,
        animate_position=100,
    )

    track = ft.Container(
        width=280,
        height=50,
        border_radius=ft.border_radius.all(25),
        bgcolor="surfaceVariant",
        content=ft.Row(
            [ft.Text("  Проведите для удаления", color="onSurfaceVariant", italic=True)],
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        animate=100,
    )

    stack = ft.Stack([track, thumb], width=280, height=50)

    def drag_start(e: ft.DragStartEvent):
        pass

    def drag_update(e: ft.DragUpdateEvent):
        max_left = (track.width or 280) - (thumb.width or 50)
        current_left = thumb.left or 0
        new_left = max(0, min(current_left + e.delta_x, max_left))
        thumb.left = new_left
        stack.update()

    def drag_end(e: ft.DragEndEvent):
        max_left = (track.width or 280) - (thumb.width or 50)
        current_left = thumb.left or 0
        if current_left >= max_left * 0.9:
            thumb.left = max_left
            thumb.content.name = "check"
            thumb.bgcolor = "green"
            stack.update()
            time.sleep(0.2)
            if on_delete_confirmed:
                on_delete_confirmed()
        else:
            thumb.left = 0
            track.bgcolor = "surfaceVariant"
            stack.update()

    return ft.GestureDetector(
        on_pan_start=drag_start,
        on_pan_update=drag_update,
        on_pan_end=drag_end,
        content=stack,
    )
