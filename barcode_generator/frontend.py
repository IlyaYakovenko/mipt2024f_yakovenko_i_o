import tkinter as tk
from tkinter import ttk, messagebox
import os
import json

def scan_directories(base_dir):
    return [f.name for f in os.scandir(base_dir) if f.is_dir()]

def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=4)
    messagebox.showinfo("Сохранение", "Настройки успешно сохранены!")


def window():
    root = tk.Tk()
    root.title("Настройки преобразований")

    base_dir = "all_outputs"
    folders = scan_directories(base_dir)

    var_rotate = tk.BooleanVar()
    var_noise = tk.BooleanVar()
    var_perspective = tk.BooleanVar()

    frame_transform = tk.LabelFrame(root, text="Выберите преобразования", padx=10, pady=10)
    frame_transform.pack(padx=10, pady=10, fill="both", expand=True)

    check_rotate = tk.Checkbutton(frame_transform, text="Поворот", variable=var_rotate)
    check_rotate.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    label_angle = tk.Label(frame_transform, text="Угол:")
    label_angle.grid(row=0, column=1, padx=5)
    entry_angle = tk.Entry(frame_transform, width=5)
    entry_angle.grid(row=0, column=2, padx=5)

    check_noise = tk.Checkbutton(frame_transform, text="Шум", variable=var_noise)
    check_noise.grid(row=1, column=0, sticky="w", padx=5, pady=5)

    label_noise = tk.Label(frame_transform, text="Интенсивность (0-255):")
    label_noise.grid(row=1, column=1, padx=5)
    entry_noise = tk.Entry(frame_transform, width=5)
    entry_noise.grid(row=1, column=2, padx=5)

    check_perspective = tk.Checkbutton(frame_transform, text="Перспективное искажение", variable=var_perspective)
    check_perspective.grid(row=2, column=0, sticky="w", padx=5, pady=5)

    frame_dirs = tk.LabelFrame(root, text="Выберите директорию", padx=10, pady=10)
    frame_dirs.pack(padx=10, pady=10, fill="both", expand=True)

    label_dirs = tk.Label(frame_dirs, text="Директория:")
    label_dirs.pack(side="left", padx=5)
    combo_dirs = ttk.Combobox(frame_dirs, values=folders, state="readonly")
    combo_dirs.pack(side="left", padx=5, fill="x", expand=True)

    button_save = tk.Button(root, text="Сохранить настройки")
    button_save.pack(pady=10)

    root.mainloop()