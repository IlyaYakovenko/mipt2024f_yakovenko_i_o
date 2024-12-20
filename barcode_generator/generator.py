import os
import json
import yaml
import re
from PIL import Image
import random
import string


class Generator:
    """
        Класс для генерации изображений кодов и разметки.
    """

    class KnowledgeBase:
        """
            База знаний для работы с типами штрихкодов и их валидацией.
        """
        def __init__(self):
            """
                Инициализирует базу знаний с поддерживаемыми типами штрихкодов и их опциями.
            """
            self.barcode_types = {"code39" : "code_39", "ean8" : "ean_8", "ean13" : "ean_13",
                         "gs1-128" : "ean_128", "interleaved2of5" :"interleaved_2_of_5",
                         "upca" : "upc_a", "upce" : "upc_e", "azteccode" : "aztec_code",
                         "datamatrix" : "data_matrix", "maxicode" : "maxi_code",
                         "pdf417" : "pdf_417", "qrcode" : "qr"}

            self.options = {"1d" : "includetext guardwhitespace", "2d" : " "}

        def validate_barcode(self, barcode_type: str, data: str) -> bool:
            """
                Проверяет соответствие данных заданному типу штрихкода.

                :param barcode_type: Тип штрихкода.
                :param data: Строка данных для валидации.
                :return: True, если данные валидны для указанного типа штрихкода.
            """
            patterns = {
                "code39": r'^[0-9A-Z\-\.\$\+\% ]+$',
                "ean8": r'^\d{7,8}$',
                "ean13": r'^\d{12,13}$',
                "upca": r'^\d{11,12}$',
                "upce": r'^\d{7,8}$',
                "interleaved2of5": r'^\d+$',
                "azteccode": r'^[\x00-\xFF]+$',
                "qrcode": r'^[\x00-\xFF]+$',
                "datamatrix": r'^[\x00-\xFF]+$',
                "pdf417": r'^[\x00-\xFF]+$',
                "maxicode": r'^[\x00-\xFF]+$',
            }

            if barcode_type.lower() == "gs1-128":
                return self.validate_gs1(data)

            pattern = patterns.get(barcode_type.lower())
            if pattern:
                return bool(re.match(pattern, data))
            else:
                raise ValueError(f"Unknown barcode type: {barcode_type}")

        def validate_gs1(self, data: str) -> bool:
            """
                Проверяет валидность данных для типа штрихкода GS1-128.

                :param data: Строка данных для валидации.
                :return: True, если данные соответствуют шаблону GS1-128.
            """
            gs1_pattern = r'^\(\d{2}\)[\x00-\xFF]+$'
            return bool(re.match(gs1_pattern, data))


    def count_black_pixel_changes_height(self, image):
        """
            Определяет изменения в количестве чёрных пикселей по высоте изображения.

            :param image: Изображение штрихкода (PIL.Image).
            :return: Координата первой строки, где произошли изменения.
        """
        image.convert("1")
        width, height = image.size

        previous_black_count = None
        change_lines = []

        for y in range(height):
            black_count = sum(1 for x in range(width) if image.getpixel((x, y)) == 0)

            if previous_black_count is not None and black_count != previous_black_count:
                change_lines.append(y)

            previous_black_count = black_count

        return change_lines[1]

    def count_black_pixel_changes_width(self, image):
        """
           Определяет изменения в количестве чёрных пикселей по ширине изображения.

           :param image: Изображение штрихкода (PIL.Image).
           :return: Координата первого столбца, где произошли изменения.
        """
        image.convert("1")
        width, height = image.size

        previous_black_count = None
        change_lines = []

        for x in range(width):
            black_count = sum(1 for y in range(height) if image.getpixel((x, y)) == 0)

            if previous_black_count is not None and black_count >= height * 0.7:
                change_lines.append(x)

            previous_black_count = black_count

        return change_lines[1]


    def get_options(self, barcode_type):
        """
            Возвращает параметры, используемые для генерации штрихкода указанного типа.

            :param barcode_type: Тип штрихкода.
            :return: Строка с опциями для генерации.
        """
        kb = self.KnowledgeBase()
        if barcode_type in ["code39", "ean8", "ean13", "gs1-128", "interleaved2of5", "upca", "upce"]:
            return kb.options["1d"]
        return kb.options["2d"]


    def format_options(self, options_str):
        """
           Преобразует строку опций в словарь для записи в yaml.

           :param options_str: Строка опций
           :return: Словарь с опциями.
        """
        options_dict = {}
        for option in options_str.split(' '):
            if option != '':
                if '=' in option:
                    key, value = option.split('=')
                    options_dict[key.strip()] = int(value.strip())
                else:
                    options_dict[option.strip()] = True
        return options_dict



    class Dumper(yaml.SafeDumper):
        """
            Расширенный дампер YAML для корректной работы с булевыми значениями.
        """
        def represent_bool(self, data):
            if data is True:
                return self.represent_scalar('tag:yaml.org,2002:bool', 'True')
            elif data is False:
                return self.represent_scalar('tag:yaml.org,2002:bool', 'False')
            return super().represent_bool(data)

    Dumper.add_representer(bool, Dumper.represent_bool)



    def generate_annotations(self, barcode_type, annotation_path, barcode_path, template_path):
        """
            Генерирует разметку для изображений штрихкодов.

            :param barcode_type: Тип штрихкода.
            :param annotation_path: Путь для сохранения разметки.
            :param barcode_path: Путь к директории с изображениями штрихкодов.
            :param template_path: Путь к файлу шаблона аннотаций.
        """
        if not os.path.exists(annotation_path):
            os.makedirs(annotation_path)

        for filename in os.listdir(barcode_path):
            if os.path.splitext(filename)[1] != ".pdf":
                file_path = os.path.join(barcode_path, filename)
                file_size = os.path.getsize(file_path)
                image = Image.open(file_path)
                width, height = image.size
                lower_bound = height
                left_bound = 0
                right_bound = width
                if barcode_type in ["ean_8", "ean_13", "upc_a", "upc_e"]:
                    left_bound = self.count_black_pixel_changes_width(image)
                    right_bound = width - left_bound
                if barcode_type in ["code_39", "ean_8", "ean_13", "ean_128", "interleaved_2_of_5", "upc_a", "upc_e"]:
                    lower_bound = self.count_black_pixel_changes_height(image)
                with open(template_path, 'r') as template_file:
                    json_data = json.load(template_file)

                json_data["_via_settings"]["project"]["name"] = filename
                file_key = f"{filename}{file_size}"

                json_data["_via_img_metadata"] = {
                    file_key: {
                        "filename": filename,
                        "size": file_size,
                        "regions": [],
                    }
                }

                json_data["_via_img_metadata"][file_key]["regions"].append({
                    "shape_attributes": {
                        "name": "polyline",
                        "all_points_x": [left_bound, right_bound, right_bound, left_bound, left_bound],
                        "all_points_y": [lower_bound, lower_bound, 0, 0, lower_bound]
                    },
                    "region_attributes": {
                        "type": barcode_type
                    }
                })
                json_data["_via_img_metadata"][file_key]["file_attributes"] = {}
                json_data["_via_attributes"]["region"]["type"]["options"][barcode_type] = ""

                json_data["_via_image_id_list"] = [file_key]

                output_filename = os.path.splitext(filename)[0] + ".json"
                output_path = os.path.join(annotation_path, output_filename)
                with open(output_path, 'w') as output_file:
                    json.dump(json_data, output_file, indent=2)


    def generate_barcode_data(self, barcode_type: str, count: int) -> list:
        """
            Генерирует данные для штрихкодов указанного типа.

            :param barcode_type: Тип штрихкода.
            :param count: Количество данных для генерации.
            :return: Список строк данных для штрихкодов.
        """
        generated_data = []

        for _ in range(count):
            if barcode_type == "code39":
                chars = string.digits + string.ascii_uppercase + "-.$+% "
                data = ''.join(random.choice(chars) for _ in range(random.randint(1, 20)))

            elif barcode_type == "ean8":
                data = ''.join(random.choice(string.digits) for _ in range(7))

            elif barcode_type == "ean13":
                data = ''.join(random.choice(string.digits) for _ in range(12))

            elif barcode_type == "upca":
                data = ''.join(random.choice(string.digits) for _ in range(11))

            elif barcode_type == "upce":
                num_sys = random.randint(0, 1)
                data = str(num_sys) + ''.join(random.choice(string.digits) for _ in range(6))

            elif barcode_type == "gs1-128":
                ai_code = "(01)"
                gtin_length = 13
                data = ai_code + ''.join(random.choice(string.digits) for _ in range(gtin_length))
                sums = 3 * sum(int(data[i]) for i in range(4, len(data), 2)) + sum(int(data[i]) for i in range(5, len(data), 2))
                control_digit = 0 if sums % 10 == 0 else 10 - sums % 10
                data += str(control_digit)

            elif barcode_type == "interleaved2of5":
                length = random.randint(1, 100)
                data = ''.join(random.choice(string.digits) for _ in range(length))

            elif barcode_type in {"azteccode", "qrcode", "datamatrix", "pdf417"}:
                length = random.randint(1, 100)
                characters = string.ascii_letters + string.digits + string.punctuation + " "
                data = ''.join(random.choices(characters, k=length)).replace(" ", "").replace("/", "")
            elif barcode_type == "maxicode":
                data = ''.join(random.choice(string.digits) for _ in range(90))
            else:
                raise ValueError(f"Неизвестный тип штрихкода: {barcode_type}")

            generated_data.append(data)

        return generated_data

