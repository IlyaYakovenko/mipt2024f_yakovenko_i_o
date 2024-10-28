import os
import json
import subprocess
import yaml
import re
from shutil import copytree


# Функция для обработки строки из файла types_data_options.txt
def parse_line(line):
    # Извлечение type, options и data с использованием регулярного выражения
    match = re.match(r"type:\s*(\w+),\s*options:\s*([\w\s=]+),\s*data:\s*\[([\d,\s]+)\]", line)
    if match:
        barcode_type = match.group(1)
        options = match.group(2)
        data = match.group(3).split(", ")
        return barcode_type, options, data
    else:
        return None, None, None


def format_options(options_str):
    options_dict = {}
    for option in options_str.split(" "):
        if '=' in option:
            key, value = option.split('=')
            options_dict[key.strip()] = int(value.strip())
        else:
            options_dict[option.strip()] = True
    return options_dict

class Dumper(yaml.SafeDumper):
    def represent_bool(self, data):
        # Записываем True/False с заглавной буквы
        if data is True:
            return self.represent_scalar('tag:yaml.org,2002:bool', 'True')
        elif data is False:
            return self.represent_scalar('tag:yaml.org,2002:bool', 'False')
        return super().represent_bool(data)

Dumper.add_representer(bool, Dumper.represent_bool)


# Функция для создания аннотационных файлов в формате JSON
def generate_annotations(barcode_type, annotation_path, barcode_path, template_path):
    if not os.path.exists(annotation_path):
        os.makedirs(annotation_path)

    for filename in os.listdir(barcode_path):
        # Получение пути и размеров файла
        if os.path.splitext(filename)[1] != "pdf":
            file_path = os.path.join(barcode_path, filename)
            file_size = os.path.getsize(file_path)

            # Чтение JSON-шаблона
            with open(template_path, 'r') as template_file:
                json_data = json.load(template_file)

            # Изменение данных в JSON в соответствии с условиями
            json_data["_via_settings"]["project"]["name"] = filename
            file_key = f"{filename}{file_size}"

            json_data["_via_img_metadata"] = {
                file_key: {
                    "filename": filename,
                    "size": file_size,
                    "regions": [],
                }
            }

            # Добавление координат точек и типа, если barcode_type == "ean13"
            if barcode_type == "ean13":
                json_data["_via_img_metadata"][file_key]["regions"].append({
                    "shape_attributes": {
                        "name": "polyline",
                        "all_points_x": [21, 214, 213, 21, 20],
                        "all_points_y": [150, 151, 5, 5, 150]
                    },
                    "region_attributes": {
                        "type": "ean_13"
                    }
                })
                json_data["_via_img_metadata"][file_key]["file_attributes"] = {}
                json_data["_via_attributes"]["region"]["type"]["options"]["ean_13"] = "EAN-13"

            json_data["_via_image_id_list"] = [file_key]

            # Сохранение JSON-файла с обновленными данными
            output_filename = os.path.splitext(filename)[0] + ".json"
            output_path = os.path.join(annotation_path, output_filename)
            with open(output_path, 'w') as output_file:
                json.dump(json_data, output_file, indent=2)


# Открываем файл types_data_options.txt и считываем строки
with open("/home/ilya/barcode_generator/types_data_options.txt", "r") as file:
    lines = file.readlines()

# Обработка каждой строки в файле types_data_options.txt
for line in lines:
    barcode_type, options, data = parse_line(line)

    if barcode_type and options and data:
        # Открываем и редактируем файл config.yaml
        with open("/home/ilya/barcode_generator/config.yaml", "r") as yaml_file:
            config = yaml.safe_load(yaml_file)

        # Обновляем значения в конфигурации
        config["barcode_type"] = barcode_type
        config["options"] = format_options(options)

        # Записываем изменения обратно в config.yaml
        with open("/home/ilya/barcode_generator/config.yaml", "w") as yaml_file:
            yaml.dump(config, yaml_file, Dumper=Dumper)

        # Открываем файл input.csv и записываем данные
        with open("/home/ilya/barcode_generator/input.csv", "w") as csv_file:
            for item in data:
                csv_file.write(f"{item}\n")

        # Запускаем команду ./start.sh после записи в input.csv
       # subprocess.run(["/home/ilya/barcode_generator/./start.sh", barcode_type])


        # Генерация аннотационных файлов в формате JSON
        annotation_path = os.path.join("all_outputs", f"{barcode_type}_annotation")
        template_path = "template.json"  # Путь к JSON-шаблону

        generate_annotations(barcode_type, annotation_path, f"all_outputs/{barcode_type}", template_path)
