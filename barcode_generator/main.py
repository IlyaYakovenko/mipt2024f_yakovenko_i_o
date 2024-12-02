from generator import Generator
from synthesizer import Synthesizer
from frontend import main_window
import subprocess
import os
import yaml
import shutil
import json

def generate_images_and_annotations(barcode_type, number, data_type):
    gnr = Generator()
    knowledge_base = gnr.KnowledgeBase()
    if data_type == "random":
        data = gnr.generate_barcode_data(barcode_type, number)
        with open("/home/ilya/barcode_generator/input.csv", "w") as csv_file:
            for item in data:
                csv_file.write(f"{item}\n")
    else:
        with open("/home/ilya/barcode_generator/input.csv", "r") as csv_file_r:
            lines = csv_file_r.readlines()
        with open("/home/ilya/barcode_generator/input.csv", "w") as csv_file_w:
            for item in lines:
                if knowledge_base.validate_barcode(barcode_type, item):
                    csv_file_w.write(f"{item}")
                else:
                    raise Exception("Wrong data: ", item)

    options = gnr.get_options(barcode_type)

    with open("/home/ilya/barcode_generator/config.yaml", "r") as yaml_file:
        config = yaml.safe_load(yaml_file)

    config["barcode_type"] = barcode_type
    config["options"] = gnr.format_options(options)

    with open("/home/ilya/barcode_generator/config.yaml", "w") as yaml_file:
        yaml.dump(config, yaml_file, Dumper=gnr.Dumper)

    try:
        subprocess.run(["/home/ilya/barcode_generator/./start.sh", barcode_type])
    except Exception as e:
        print(e)

    annotation_path = os.path.join("all_outputs", f"{barcode_type}_annotation")
    template_path = "template.json"

    gnr.generate_annotations(knowledge_base.barcode_types[barcode_type], annotation_path, f"all_outputs/{barcode_type}", template_path)

def make_transformation(image, annotation, barcode_type, type_transform, params):
    snt = Synthesizer(image, annotation, barcode_type)
    file_path_to_save = f"transformed_codes/{barcode_type}_{type_transform}/"
    ann_path_to_save = f"transformed_codes/{barcode_type}_{type_transform}_annotation/"
    os.makedirs(file_path_to_save, exist_ok=True)
    os.makedirs(ann_path_to_save, exist_ok=True)
    width = snt.image.width
    height = snt.image.height
    orig_points = [(0, 0), (width, 0), (width, height), (0, height)]
    transformed_image = None
    transformed_coords = None
    new_name = f"/{os.path.splitext(os.path.basename(image))[0]}"
    if type_transform == "rotate":
        transformed_image, transformed_coords = snt.rotate(int(params["angle"]))
        new_name += "_rotated.png"
    if type_transform == "perspective":
        if params["type"] == "Down view":
            dst_points = [(-width * 0.3, 0), (width * 1.3, 0), (width, height), (0, height)]
            transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
            new_name += "_perspective.png"
        if params["type"] == "Top view":
            dst_points = [(0, 0), (width, 0), (width * 1.3, height), (-width * 0.3, height)]
            transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
            new_name += "_perspective.png"
        if params["type"] == "Left view":
            dst_points = [(0, 0), (width, -height * 0.3), (width, height * 1.3), (0, height)]
            transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
            new_name += "_perspective.png"
        if params["type"] == "Right view":
            dst_points = [(0, -height * 0.3), (width, 0), (width, height), (0, 1.3 * height)]
            transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
            new_name  += "_perspective.png"
    if type_transform == "noise":
        transformed_image, transformed_coords = snt.add_noise(int(params["intensity"]))
        new_name += "_noised.png"
    if type_transform == "zoom":
        transformed_image, transformed_coords = snt.zoom(int(params["degree"]))
        new_name += "_scaled.png"
    if type_transform == "blur":
        transformed_image, transformed_coords = snt.add_blur(int(params["degree"]))
        new_name += "_blured.png"
    if type_transform == "texture":
        transformed_image, transformed_coords = snt.add_texture(params["texture_file"])
        new_name = "_textured.png"
    if type_transform == "glare":
        transformed_image, transformed_coords = snt.add_glare(int(params["intensity"]), int(params["radius"]), int(params["position"]))
        new_name += "_with_glare.png"
    if type_transform == "brightness":
        transformed_image, transformed_coords = snt.adjust_brightness(int(params["degree"]))
        new_name += "_brightness.png"
    if type_transform == "contrast":
        transformed_image, transformed_coords = snt.adjust_contrast(int(params["degree"]))
        new_name += "_contrast.png"
    if type_transform == "saturation":
        transformed_image, transformed_coords = snt.adjust_saturation(int(params["degree"]))
        new_name += "_saturation.png"

    if transformed_image and transformed_coords:
        transformed_image.save(file_path_to_save + new_name, format="PNG")
        shutil.move(transformed_coords, os.path.join(ann_path_to_save, transformed_coords))
    else:
        print("Не было выполнено преобразований")

def process_settings_file():
    # Загрузка настроек из файла
    if not os.path.exists("settings.json"):
        print("Файл настроек не найден!")
        return

    with open("settings.json", "r") as f:
        settings = json.load(f)

    # Если выбрано "сгенерировать коды"
    if "code_type" in settings:
        generate_images_and_annotations(settings["code_type"], settings["code_count"], settings["data_type"])
        return

    # Если выбрано "преобразовать готовые коды"
    if "codes_directory" in settings:
        barcode_path = settings["codes_directory"]
        current_image_dir = barcode_path
        if not os.path.exists(current_image_dir):
            print(f"Директория с кодами '{current_image_dir}' не найдена!")
            return

        # Получение списка файлов
        files = os.listdir(current_image_dir)
        image_files = [file for file in files if file.endswith((".png", ".jpg", ".jpeg", ".bmp"))]

        # Проверка наличия изображений
        if not image_files:
            print("Изображения для преобразования не найдены!")
            return

        # Итерация по изображениям и последовательное применение преобразований
        for transform_type, transform_params in settings.items():
            if not isinstance(transform_params, dict) or not transform_params.get("enabled", False):
                continue

            for filename in image_files:
                file_path = os.path.join(current_image_dir, filename)

                annotation = current_image_dir + "_annotation/" + os.path.splitext(filename)[0] + ".json"
                if not os.path.exists(annotation):
                    print(f"Аннотация для {filename} не найдена, пропуск...")
                    continue

                # Вызов преобразований
                make_transformation(
                    file_path,
                    annotation,
                    barcode_path.split("/")[-1],
                    transform_type,
                    transform_params
                )


if __name__ == "__main__":
    main_window()
    process_settings_file()