import os
import json
import yaml
import re
from PIL import Image
import random
import string


class Generator:

    class KnowledgeBase:

        def __init__(self):
            self.barcode_types = {"39": ["code39", "code_39"], "8" : ["ean8", "ean_8"], "13": ["ean13", "ean_13"],
                         "128": ["gs1-128", "ean_128"], "2of5": ["interleaved2of5", "interleaved_2_of_5"],
                         "upca": ["upca", "upc_a"], "upce": ["upce", "upc_e"], "aztec": ["azteccode", "aztec_code"],
                         "matrix": ["datamatrix", "data_matrix"], "maxi": ["maxicode", "maxi_code"],
                         "417": ["pdf417", "pdf_417"], "qr": ["qrcode", "qr"]}

        def validate_barcode(self, barcode_type: str, data: str) -> bool:
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
            gs1_pattern = r'^\(\d{2}\)[\x00-\xFF]+$'
            sums = 3 * sum(int(data[i]) for i in range(4, len(data), 2)) + sum(int(data[i]) for i in range(5, len(data), 2))
            control_digit = 0 if sums % 10 == 0 else 10 - sums % 10
            return True
            return bool(re.match(gs1_pattern, data)) and str(data[-1]) == control_digit


    def count_black_pixel_changes(self, image):
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


    def parse_line(self, line):
        match = re.match(r"\s*options:\s*([\w\s=,]*)\s*data:\s*\[([\d,\s]+)\]", line)
        if match:
            options = match.group(1)
            data = match.group(2).split(", ")
            return options, data
        else:
            return None, None


    def format_options(self, options_str):
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
        def represent_bool(self, data):
            if data is True:
                return self.represent_scalar('tag:yaml.org,2002:bool', 'True')
            elif data is False:
                return self.represent_scalar('tag:yaml.org,2002:bool', 'False')
            return super().represent_bool(data)

    Dumper.add_representer(bool, Dumper.represent_bool)



    def generate_annotations(self, barcode_type, annotation_path, barcode_path, template_path):
        if not os.path.exists(annotation_path):
            os.makedirs(annotation_path)

        for filename in os.listdir(barcode_path):
            if os.path.splitext(filename)[1] != ".pdf":
                file_path = os.path.join(barcode_path, filename)
                file_size = os.path.getsize(file_path)
                image = Image.open(file_path)
                width, height = image.size
                lower_bound = height
                if barcode_type in ["code_39", "ean_8", "ean_13", "ean_128", "interleaved_2_of_5", "upc_a", "upc_e"]:
                    lower_bound = self.count_black_pixel_changes(image)
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
                        "all_points_x": [0, width, width, 0, 0],
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

