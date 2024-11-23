import os
import numpy as np
import random
from PIL import Image, ImageFilter, ImageDraw, ImageEnhance
import json
import math


class Synthesizer:
    def __init__(self, image_path, annotation_path, barcode_type):
        self.image = Image.open(image_path)
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
        file_size = os.path.getsize(self.image_path)
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
                "type": self.barcode_type
            }
        })

        data["_via_img_metadata"][file_key]["file_attributes"] = {}
        data["_via_attributes"]["region"]["type"]["options"][self.barcode_type] = ""
        data["_via_image_id_list"] = [file_key]


        with open(output_filename, 'w') as output_file:
            json.dump(data, output_file, indent=2)
        return output_filename

    def rotate(self, angle):
        rotated_img = self.image.rotate(angle, expand=True)
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

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_rotated.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_rotated.json"

        return rotated_img, self.create_new_json(rotated_coords, new_image_name, output_filename)

    def change_perspective(self, src_points, dst_points):
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
        matrix = []
        for (x, y), (x_prime, y_prime) in zip(src_points, dst_points):
            matrix.append([x, y, 1, 0, 0, 0, -x_prime * x, -x_prime * y])
            matrix.append([0, 0, 0, x, y, 1, -y_prime * x, -y_prime * y])

        A = np.array(matrix, dtype=np.float64)
        B = np.array(dst_points).flatten()
        res = np.linalg.solve(A, B)
        return res.flatten()

    def zoom(self):
        sx, sy = 1.3, 1.3
        scaling_matrix = (sx, 0, 0, 0, sy, 0)
        scaled = self.image.transform((int(self.image.width * sx), int(self.image.height * sy)), Image.AFFINE, scaling_matrix)

        scaled_coords = []
        scaling_matrix = np.linalg.inv(np.array([
            [sx, 0, 0],
            [0, sy, 0],
            [0, 0, 1]
        ]))
        for x, y in self.annotation_coordinates:
            vec = np.array([x, y, 1])
            transformed = np.dot(scaling_matrix, vec)
            if transformed[2] == 0:
                x_new, y_new = 0, 0
            else:
                x_new, y_new = transformed[0] / transformed[2], transformed[1] / transformed[2]
            scaled_coords.append((x_new, y_new))

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_scaled.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_scaled.json"
        return scaled, self.create_new_json(scaled_coords, new_image_name, output_filename)

    def add_noise(self, intensity=30):
        np_image = np.asarray(self.image.convert("L"))
        noise = np.random.randint(-intensity, intensity, np_image.shape)
        noisy_image = np.clip(np_image + noise, 0, 255).astype('uint8')

        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_noised.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_noised.json"
        return Image.fromarray(noisy_image), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_blur(self, radius=1):
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_blured.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_blured.json"
        return self.image.convert("L").filter(ImageFilter.GaussianBlur(radius)), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_texture(self, texture_path):
        texture = Image.open(texture_path).convert("L").resize(self.image.size)
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_textured.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_textured.json"
        return Image.blend(self.image.convert("L"), texture, alpha=0.5), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def add_glare(self, intensity=0.5, radius=100, position=None):
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
        enhancer = ImageEnhance.Brightness(self.image.convert("L"))
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_brightness.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_brightness.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def adjust_contrast(self, factor=0.3):
        enhancer = ImageEnhance.Contrast(self.image.convert("L"))
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_contrast.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_contrast.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)

    def adjust_saturation(self, factor=0.3):
        enhancer = ImageEnhance.Color(self.image.convert("L"))
        new_image_name = f"{os.path.splitext(os.path.basename(self.image_path))[0]}_saturation.png"
        output_filename = os.path.splitext(os.path.basename(self.annotation))[0] + "_saturation.json"
        return enhancer.enhance(factor), self.create_new_json(self.annotation_coordinates, new_image_name, output_filename)