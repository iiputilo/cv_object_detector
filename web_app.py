import flet as ft
import threading
import core_functions
from core_functions import *

def main(page: ft.Page):
    page.title = "iiputilo's Objects Detection App"
    init_db()

    video_img = ft.Image()
    detections_table = ft.DataTable(
        columns=[ft.DataColumn(ft.Text("Время")), ft.DataColumn(ft.Text("Объект"))],
        rows=[]
    )

    def refresh_table():
        """Обновляет таблицу обнаруженных объектов"""
        rows = load_detections()[:100]
        detections_table.rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(r[0])), ft.DataCell(ft.Text(r[1]))])
            for r in rows
        ]
        page.update()

    # Чекбокс для включения/выключения обнаружения объектов
    checkbox = ft.Checkbox(label="Включить YOLO", value=False)
    def toggle_detection(e):
        core_functions.detect_flag = checkbox.value
    checkbox.on_change = toggle_detection

    # Обертка для таблицы
    table_container = ft.Column(
        controls=[detections_table],
        scroll=ft.ScrollMode.AUTO,
        height=500
    )

    # Поля для фильтрации по времени
    start_time_input = ft.TextField(label="Начальное время (HH:MM:SS)")
    end_time_input = ft.TextField(label="Конечное время (HH:MM:SS)")
    filter_button = ft.ElevatedButton(text="Фильтровать")

    def refresh_table_filtered(e):
        """Обновляет таблицу по заданному временному диапазону"""
        st = start_time_input.value.strip()
        et = end_time_input.value.strip()
        query = (
            "SELECT time, object_name FROM detections "
            "WHERE time >= ? AND time <= ? ORDER BY id DESC"
        )
        conn = sqlite3.connect(db_file)
        cur = conn.cursor()
        cur.execute(query, (st, et))
        rows = cur.fetchall()
        conn.close()
        detections_table.rows = [
            ft.DataRow(cells=[ft.DataCell(ft.Text(r[0])), ft.DataCell(ft.Text(r[1]))])
            for r in rows
        ]
        page.update()

    left_section = ft.Column([video_img, checkbox])
    right_section = table_container
    page.add(ft.Row([left_section, right_section]))

    # Фоновый поток для видео с камеры
    t = threading.Thread(target=capture_frames, args=(video_img, page, refresh_table), daemon=True)
    t.start()

    filter_button.on_click = refresh_table_filtered
    filters_row = ft.Row([start_time_input, end_time_input, filter_button])
    page.add(filters_row)

ft.app(target=main, view=ft.WEB_BROWSER)