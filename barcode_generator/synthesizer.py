import os
import numpy as np
import random
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import json
import math

from generator import Generator
gnr = Generator()
knowledge_base = gnr.KnowledgeBase()

def find_line(x1, y1, x2, y2):
    """
        Вычисляет параметры прямой линии (угловой коэффициент и смещение).

        :param x1: Координата x первой точки.
        :param y1: Координата y первой точки.
        :param x2: Координата x второй точки.
        :param y2: Координата y второй точки.
        :return: Угловой коэффициент (m) и смещение (b).
    """
    m = (y2 - y1) / (x2 - x1)
    b = y1 - m * x1
    return m, b

class Synthesizer:
    """
        Класс для выполнения различных преобразований над изображениями штрихкодов и разметкой.
    """
    def __init__(self, image_path, annotation_path, barcode_type):
        """
            Инициализация класса Synthesizer.

            :param image_path: Путь к изображению штрихкода.
            :param annotation_path: Путь к файлу разметки.
            :param barcode_type: Тип штрихкода.
        """
        self.image = Image.open(image_path).convert("RGBA")
        self.annotation = annotation_path
        self.image_path = image_path
        self.barcode_type = barcode_type
        with open(annotation_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        coordinates = []
        file_key = list(data.get("_via_img_metadata").keys())[0]
        regions = data["_via_img_metadata"][file_key]["regions"][0]["shape_attributes"]
        if regions:
            all_points_x = regions.get("all_points_x", [])
            all_points_y = regions.get("all_points_y", [])
            coordinates = list(zip(all_points_x, all_points_y))
        self.annotation_coordinates = coordinates
        os.makedirs("transformed_codes", exist_ok=True)

    def create_new_json(self, coords, new_image_name, output_filename):
        """
            Создаёт файл разметки для преобразованного изображения.

            :param coords: Координаты области кода на изображении.
            :param new_image_name: Имя нового изображения.
            :param output_filename: Имя файла для сохранения разметки.
            :return: Имя выходного файла разметки.
        """
        file_size = os.path.getsize(self.image_path)
        type_in_ann = knowledge_base.barcode_types[self.barcode_type.split("_")[0]]
        with open(self.annotation, 'r') as template_file:
            data = json.load(template_file)

        data["_via_settings"]["project"]["name"] = new_image_name

        file_key = f"{new_image_name}{file_size}"

        data["_via_img_metadata"] = {
            file_key: {
                "filename": new_image_name,
                "size": file_size,
                "regions": [],
            }
        }

        data["_via_img_metadata"][file_key]["regions"].append({
            "shape_attributes" : {
                "name": "polyline",
                "all_points_x": [coords[i][0] for i in range(len(coords))],
                "all_points_y": [coords[i][1] for i in range(len(coords))]
            },
            "region_attributes": {
                "type": type_in_ann
            }
        })

        data["_via_img_metadata"][file_key]["file_attributes"] = {}
        data["_via_attributes"]["region"]["type"]["options"][type_in_ann] = ""
        data["_via_image_id_list"] = [file_key]


        with open(output_filename, 'w') as output_file:
            json.dump(data, output_file, indent=2)
        return output_filename

    def rotate(self, angle):
        """
            Поворачивает изображение на заданный угол.

            :param angle: Угол поворота в градусах.
            :return: Повернутое изображение и новый файл разметки.
        """
        rotated_img = self.image.rotate(angle, expand=True, resample=Image.BICUBIC)
        angle_rad = -math.radians(angle)
        x_c = self.image.width / 2
        y_c = self.image.height / 2
        rotated_coords = []

        for x, y in self.annotation_coordinates:
            x_local = x - x_c
            y_local = y - y_c

            x_rot = x_local * math.cos(angle_rad) - y_local * math.sin(angle_rad)
            y_rot = x_local * math.sin(angle_rad) + y_local * math.cos(angle_rad)

            shift_x = (rotated_img.width - self.image.width) / 2
            shift_y = (rotated_img.height - self.image.height) / 2

            x_new = x_rot + x_c + shift_x
            y_new = y_rot + y_c + shift_y
            rotated_coords.append((x_new, y_new))

        # m0, b0 = find_line(*rotated_coords[0], *rotated_coords[1])
        # m1, b1 = find_line(*rotated_coords[1], *rotated_coords[2])
        # m2, b2 = find_line(*rotated_coords[2], *rotated_coords[3])
        # m3, b3 = find_line(*rotated_coords[3], *rotated_coords[0])
        # for x in range(rotated_img.width):
        #     for y in range(rotated_img.height):
        #         line_0 = m0 * x + b0
        #         line_1 = m1 * x + b1
        #         line_2 = m2 * x + b2
        #         line_3 = m3 * x + b3
        #         if y > line_1:  # Если пиксель вне границы
        #             coordinate = x, y
        #             r, g, b, a = rotated_img.getpixel(coordinate)
        #             if r == 0 and g == 0 and b == 0:  # Если пиксель черный
        #                 rotated_img.putpixel((x, y), (255, 255, 255, 1))

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_rotated.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_rotated.json"

        return rotated_img, self.create_new_json(rotated_coords, new_image_name, output_filename)

    def change_perspective(self, src_points, dst_points):
        """
            Осуществляет проективное искажение.

            :param src_points: Исходные вершины изображения.
            :param dst_points: Целевые точки для преобразования.
            :return: Изображение с изменённой перспективой и новый файл разметки.
        """
        coeffs = self.find_perspective_coeffs(src_points, dst_points)

        transformed_image = self.image.transform(self.image.size, Image.PERSPECTIVE, coeffs, Image.BICUBIC)

        transformed_coords = []
        matrix = np.array([
            [coeffs[0], coeffs[1], coeffs[2]],
            [coeffs[3], coeffs[4], coeffs[5]],
            [coeffs[6], coeffs[7], 1]
        ])
        matrix = np.linalg.inv(matrix)
        for x, y in self.annotation_coordinates:
            vec = np.array([x, y, 1])
            transformed = np.dot(matrix, vec)
            x_new, y_new = transformed[0] / transformed[2], transformed[1] / transformed[2]
            transformed_coords.append((x_new, y_new))

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_perspective.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_perspective.json"
        return transformed_image, self.create_new_json(transformed_coords, new_image_name, output_filename)

    def find_perspective_coeffs(self, src_points, dst_points):
        """
            Вычисляет коэффициенты для перспективного преобразования.

            :param src_points: Исходные точки.
            :param dst_points: Целевые точки.
            :return: Список коэффициентов для преобразования.
        """
        matrix = []
        for (x, y), (x_prime, y_prime) in zip(src_points, dst_points):
            matrix.append([x, y, 1, 0, 0, 0, -x_prime * x, -x_prime * y])
            matrix.append([0, 0, 0, x, y, 1, -y_prime * x, -y_prime * y])

        A = np.array(matrix, dtype=np.float64)
        B = np.array(dst_points).flatten()
        res = np.linalg.solve(A, B)
        return res.flatten()

    def zoom(self, degree):
        """
            Изменяет масштаб изображения.

            :param degree: Степень масштабирования.
            :return: Масштабированное изображение и новый файл разметки.
        """
        sx, sy = degree, degree
        scaled = self.image.resize((int(self.image.width * sx), int(self.image.height * sy)), resample=Image.LANCZOS)
        scaled_coords = [(x * sx, y * sy) for x, y in self.annotation_coordinates]

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_scaled.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_scaled.json"
        return scaled, self.create_new_json(scaled_coords, new_image_name, output_filename)

    def add_noise(self, intensity=30):
        """
            Добавляет шум к изображению.

            :param intensity: Интенсивность шума.
            :return: Изображение с шумом и новый файл разметки.
        """
        np_image = np.asarray(self.image.convert("L"))
        noise = np.random.randint(-intensity, intensity, np_image.shape)
        noisy_image = np.clip(np_image + noise, 0, 255).astype('uint8')

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_noised.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_noised.json"
        return Image.fromarray(noisy_image), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_blur(self, radius=1):
        """
            Добавляет размытие изображению.

            :param radius: Радиус размытия.
            :return: Размытое изображение и новый файл разметки.
        """
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_blured.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_blured.json"
        return self.image.convert("L").filter(ImageFilter.GaussianBlur(radius)), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_texture(self, texture_path):
        """
            Добавляет текстуру на изображение.

            :param texture_path: Путь к изображению текстуры.
            :return: Изображение с текстурой и новый файл разметки.
        """
        texture = Image.open(texture_path).convert("L").resize(self.image.size)
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_textured.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_textured.json"
        return Image.blend(self.image.convert("L"), texture, alpha=0.5), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_glare(self, intensity=0.5, radius=100, position=None):
        """
           Добавляет эффект блика на изображение.

           :param intensity: Интенсивность блика (от 0 до 1).
           :param radius: Радиус блика.
           :param position: Координаты центра блика (по умолчанию случайное).
           :return: Изображение с бликом и новый файл разметки.
        """
        width, height = self.image.size
        if position is None:
            position = (random.randint(0, width), random.randint(0, height))

        glare = Image.new("RGBA", (width, height), (255, 255, 255, 0))
        draw = ImageDraw.Draw(glare)

        for r in range(radius, 0, -1):
            alpha = int(255 * (1 - r / radius) * intensity)
            draw.ellipse([
                (position[0] - r, position[1] - r),
                (position[0] + r, position[1] + r)
            ], fill=(255, 255, 255, alpha))

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_with_glare.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_with_glare.json"
        return Image.alpha_composite(self.image.convert("RGBA"), glare).convert("RGB"), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def adjust_brightness(self, factor=0.3):
        """
            Регулирует яркость изображения.

            :param factor: Коэффициент изменения яркости.
            :return: Изображение с изменённой яркостью и новый файл разметки.
        """
        enhancer = ImageEnhance.Brightness(self.image)
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_brightness.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_brightness.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def adjust_contrast(self, factor=0.3):
        """
            Регулирует контрастность изображения.

            :param factor: Коэффициент изменения контрастности.
            :return: Изображение с изменённым контрастом и новый файл разметки.
        """
        enhancer = ImageEnhance.Contrast(self.image)
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_contrast.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_contrast.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def adjust_saturation(self, factor=0.3):
        """
            Регулирует насыщенность изображения.

            :param factor: Коэффициент изменения насыщенности.
            :return: Изображение с изменённой насыщенностью и новый файл разметки.
        """
        enhancer = ImageEnhance.Color(self.image)
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_saturation.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_saturation.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def overlay_barcode_on_background(self, background_image_path, x_off, y_off):
        """
            Накладывает изображение штрихкода на фон.

            :param background_image_path: Путь к изображению фона.
            :param x_off: Смещение по оси X.
            :param y_off: Смещение по оси Y.
            :return: Изображение с наложением и новый файл разметки.
        """
        background = Image.open(background_image_path)

        x = background.size[0] // 2
        y = background.size[1] // 2

        background = Image.alpha_composite(
            Image.new("RGBA", background.size),
            background.convert('RGBA')
        )

        background.paste(
            self.image,
            (x + x_off, y + y_off),
            self.image
        )

        new_coords = [(x_orig + x_off + x, y_orig + y_off + y) for x_orig, y_orig in self.annotation_coordinates]


        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_pasted.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_pasted.json"
        return background, self.create_new_json(new_coords, new_image_name, output_filename)