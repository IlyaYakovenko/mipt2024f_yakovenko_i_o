import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import json


def save_settings(settings):
    with open("settings.json", "w") as f:
        json.dump(settings, f, indent=4)
    messagebox.showinfo("Сохранение", "Настройки успешно сохранены!")


def choose_file():
    file_path = filedialog.askopenfilename(title="Выберите файл текстуры")
    return file_path


def select_directory():
    return filedialog.askdirectory(title="Выберите директорию")


def transform_existing_codes():
    root = tk.Tk()
    root.title("Преобразовать готовые коды")

    codes_directory = tk.StringVar()

    def choose_codes_directory():
        directory = select_directory()
        if directory:
            codes_directory.set(directory)

    var_rotate = tk.BooleanVar()
    var_noise = tk.BooleanVar()
    var_perspective = tk.BooleanVar()
    var_scale = tk.BooleanVar()
    var_blur = tk.BooleanVar()
    var_brightness = tk.BooleanVar()
    var_contrast = tk.BooleanVar()
    var_saturation = tk.BooleanVar()
    var_glare = tk.BooleanVar()
    var_texture = tk.BooleanVar()

    settings = {}

    def save_transform_settings():
        settings["codes_directory"] = codes_directory.get()
        settings["rotate"] = {"enabled": var_rotate.get(), "angle": entry_angle.get()}
        settings["noise"] = {"enabled": var_noise.get(), "intensity": entry_noise.get()}
        settings["perspective"] = {
            "enabled": var_perspective.get(),
            "type": combo_perspective.get(),
            #"degree": entry_perspective.get(),
        }
        settings["scale"] = {"enabled": var_scale.get(), "degree": entry_scale.get()}
        settings["blur"] = {"enabled": var_blur.get(), "degree": entry_blur.get()}
        settings["brightness"] = {"enabled": var_brightness.get(), "degree": entry_brightness.get()}
        settings["contrast"] = {"enabled": var_contrast.get(), "degree": entry_contrast.get()}
        settings["saturation"] = {"enabled": var_saturation.get(), "degree": entry_saturation.get()}
        settings["glare"] = {
            "enabled": var_glare.get(),
            "intensity": entry_glare_intensity.get(),
            "radius": entry_glare_radius.get(),
            "position": entry_glare_position.get(),
        }
        settings["texture"] = {"enabled": var_texture.get(), "texture_file" : texture_file_var.get()}
        save_settings(settings)
        root.destroy()

    frame_transform = tk.LabelFrame(root, text="Выберите преобразования", padx=10, pady=10)
    frame_transform.pack(padx=10, pady=10, fill="both", expand=True)

    check_perspective = tk.Checkbutton(frame_transform, text="Проективное искажение", variable=var_perspective)
    check_perspective.grid(row=0, column=0, sticky="w", padx=5, pady=5)

    label_perspective_type = tk.Label(frame_transform, text="Тип:")
    label_perspective_type.grid(row=0, column=1, padx=5)
    combo_perspective = ttk.Combobox(frame_transform, values=["Down view", "Top view", "Left view", "Right view"], state="readonly")
    combo_perspective.grid(row=0, column=2, padx=5)

    # label_perspective_degree = tk.Label(frame_transform, text="Степень:")
    # label_perspective_degree.grid(row=0, column=3, padx=5)
    # entry_perspective = tk.Entry(frame_transform, width=5)
    # entry_perspective.grid(row=0, column=4, padx=5)

    check_rotate = tk.Checkbutton(frame_transform, text="Поворот", variable=var_rotate)
    check_rotate.grid(row=1, column=0, sticky="w", padx=5, pady=5)

    label_angle = tk.Label(frame_transform, text="Угол:")
    label_angle.grid(row=1, column=1, padx=5)
    entry_angle = tk.Entry(frame_transform, width=5)
    entry_angle.grid(row=1, column=2, padx=5)

    check_noise = tk.Checkbutton(frame_transform, text="Шум", variable=var_noise)
    check_noise.grid(row=2, column=0, sticky="w", padx=5, pady=5)

    label_noise = tk.Label(frame_transform, text="Интенсивность (0-255):")
    label_noise.grid(row=2, column=1, padx=5)
    entry_noise = tk.Entry(frame_transform, width=5)
    entry_noise.grid(row=2, column=2, padx=5)

    check_scale = tk.Checkbutton(frame_transform, text="Масштаб", variable=var_scale)
    check_scale.grid(row=3, column=0, sticky="w", padx=5, pady=5)

    label_scale = tk.Label(frame_transform, text="Коэффициент масштабирования:")
    label_scale.grid(row=3, column=1, padx=5)
    entry_scale = tk.Entry(frame_transform, width=5)
    entry_scale.grid(row=3, column=2, padx=5)

    check_blur = tk.Checkbutton(frame_transform, text="Размытие", variable=var_blur)
    check_blur.grid(row=4, column=0, sticky="w", padx=5, pady=5)

    label_blur = tk.Label(frame_transform, text="Глубина размытия:")
    label_blur.grid(row=4, column=1, padx=5)
    entry_blur = tk.Entry(frame_transform, width=5)
    entry_blur.grid(row=4, column=2, padx=5)

    check_brightness = tk.Checkbutton(frame_transform, text="Яркость", variable=var_brightness)
    check_brightness.grid(row=5, column=0, sticky="w", padx=5, pady=5)

    label_brightness = tk.Label(frame_transform, text="Уровень яркости:")
    label_brightness.grid(row=5, column=1, padx=5)
    entry_brightness = tk.Entry(frame_transform, width=5)
    entry_brightness.grid(row=5, column=2, padx=5)

    check_contrast = tk.Checkbutton(frame_transform, text="Контрастность", variable=var_contrast)
    check_contrast.grid(row=6, column=0, sticky="w", padx=5, pady=5)

    label_contrast = tk.Label(frame_transform, text="Глубина контраста:")
    label_contrast.grid(row=6, column=1, padx=5)
    entry_contrast = tk.Entry(frame_transform, width=5)
    entry_contrast.grid(row=6, column=2, padx=5)

    check_saturation = tk.Checkbutton(frame_transform, text="Насыщенность", variable=var_saturation)
    check_saturation.grid(row=7, column=0, sticky="w", padx=5, pady=5)

    label_saturation = tk.Label(frame_transform, text="Интенсивность цветов:")
    label_saturation.grid(row=7, column=1, padx=5)
    entry_saturation = tk.Entry(frame_transform, width=5)
    entry_saturation.grid(row=7, column=2, padx=5)

    check_glare = tk.Checkbutton(frame_transform, text="Блик", variable=var_glare)
    check_glare.grid(row=8, column=0, sticky="w", padx=5, pady=5)

    label_glare_intensity = tk.Label(frame_transform, text="Интенсивность:")
    label_glare_intensity.grid(row=8, column=1, padx=5)
    entry_glare_intensity = tk.Entry(frame_transform, width=5)
    entry_glare_intensity.grid(row=8, column=2, padx=5)

    label_glare_radius = tk.Label(frame_transform, text="Радиус:")
    label_glare_radius.grid(row=9, column=1, padx=5)
    entry_glare_radius = tk.Entry(frame_transform, width=5)
    entry_glare_radius.grid(row=9, column=2, padx=5)

    label_glare_position = tk.Label(frame_transform, text="Позиция:")
    label_glare_position.grid(row=10, column=1, padx=5)
    entry_glare_position = tk.Entry(frame_transform, width=5)
    entry_glare_position.grid(row=10, column=2, padx=5)

    check_texture = tk.Checkbutton(frame_transform, text="Текстура", variable=var_texture)
    check_texture.grid(row=11, column=0, sticky="w", padx=5, pady=5)
    texture_file_var = tk.StringVar()
    btn_select_texture = tk.Button(frame_transform, text="Выбрать текстуру", command=lambda: texture_file_var.set(choose_file()))
    btn_select_texture.grid(row=11, column=1, padx=5, pady=5)

    btn_select_codes_dir = tk.Button(root, text="Выбрать директорию с кодами", command=choose_codes_directory)
    btn_select_codes_dir.pack(padx=10, pady=11)

    frame_transform = tk.LabelFrame(root, text="Выберите преобразования", padx=10, pady=10)
    frame_transform.pack(padx=10, pady=11, fill="both", expand=True)

    button_save = tk.Button(root, text="Сохранить настройки", command=save_transform_settings)
    button_save.pack(pady=10)

    root.mainloop()


def generate_and_transform_codes():
    root = tk.Tk()
    root.title("Сгенерировать и преобразовать коды")
    code_type = tk.StringVar()
    code_count = tk.IntVar()
    data_type = tk.StringVar()

    settings = {}

    def save_generate_settings():
        settings["code_type"] = code_type.get()
        settings["code_count"] = code_count.get()
        settings["data_type"] = data_type.get()
        save_settings(settings)
        root.destroy()

    # Выбор типа кода
    tk.Label(root, text="Тип кода:").pack(padx=10, pady=5)
    combo_code_type = ttk.Combobox(root, textvariable=code_type, values=[
        "code39", "ean8", "ean13", "upca", "upce",
        "interleaved2of5", "azteccode", "qrcode",
        "datamatrix", "pdf417", "maxicode"
    ], state="readonly")
    combo_code_type.pack(padx=10, pady=5)

    # Выбор количества кодов
    tk.Label(root, text="Количество кодов:").pack(padx=10, pady=5)
    spin_code_count = tk.Spinbox(root, from_=1, to=1000, textvariable=code_count, width=5)
    spin_code_count.pack(padx=10, pady=5)

    # Выбор данных
    frame_data = tk.LabelFrame(root, text="Тип данных", padx=10, pady=10)
    frame_data.pack(padx=10, pady=10, fill="both", expand=True)

    radio_random = tk.Radiobutton(frame_data, text="Случайные данные", value="random", variable=data_type)
    radio_random.pack(anchor="w")

    radio_custom = tk.Radiobutton(frame_data, text="Собственные данные", value="custom", variable=data_type)
    radio_custom.pack(anchor="w")

    button_save = tk.Button(root, text="Сохранить настройки", command=save_generate_settings)
    button_save.pack(pady=10)
    root.mainloop()


def main_window():
    root = tk.Tk()
    root.title("Выберите опцию")

    def open_transform_existing():
        root.destroy()
        transform_existing_codes()

    def open_generate_and_transform():
        root.destroy()
        generate_and_transform_codes()


    btn_generate_and_transform = tk.Button(root, text="Сгенерировать коды", command=open_generate_and_transform)
    btn_generate_and_transform.pack(padx=10, pady=10)

    btn_transform_existing = tk.Button(root, text="Преобразовать готовые коды", command=open_transform_existing)
    btn_transform_existing.pack(padx=10, pady=10)

    root.mainloop()
