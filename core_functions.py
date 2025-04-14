import sqlite3
import cv2
import base64
import random
from ultralytics import YOLO
import time

detect_flag = False
db_file = "detections.db" # Путь к файлу БД
model = YOLO("yolo11n.pt")
color_map = {}


def init_db():
    """Создает таблицу для хранения детекций"""
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS detections (id INTEGER PRIMARY KEY AUTOINCREMENT, time TEXT, object_name TEXT)"
    )
    conn.commit()
    conn.close()

def load_detections():
    """Загружает все детекции из БД"""
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("SELECT time, object_name FROM detections ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def insert_detection(object_name):
    """Добавляет новую запись с названием найденного объекта"""
    conn = sqlite3.connect(db_file)
    cur = conn.cursor()
    cur.execute("INSERT INTO detections (time, object_name) VALUES (?, ?)",
                (time.strftime("%H:%M:%S"), object_name))
    conn.commit()
    conn.close()

def get_object_color(label):
    """Определяет уникальный цвет для каждого класса"""
    if label not in color_map:
        color_map[label] = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255)
        )
    return color_map[label]


def capture_frames(video_img, page, refresh_table):
    """Захватывает кадры с веб-камеры и проводит детекцию"""
    global detect_flag
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            continue
        if detect_flag:
            results = model(frame)
            for r in results:
                for box in r.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    label = r.names[int(box.cls[0])]
                    color = get_object_color(label)
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
                    insert_detection(label)
            refresh_table()
        _, encoded = cv2.imencode(".jpg", frame)
        video_img.src_base64 = base64.b64encode(encoded).decode("utf-8")
        page.update()
    cap.release()
