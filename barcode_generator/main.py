from generator import Generator
from synthesizer import Synthesizer
import subprocess
import os
import yaml
import shutil


def generate_images_and_annotations():
    gnr = Generator()
    with open("/home/ilya/barcode_generator/types_data_options.txt", "r") as file:
        lines = file.readlines()

    knowledge_base = gnr.KnowledgeBase()

    for line, value in zip(lines, knowledge_base.barcode_types.values()):
        barcode_type = value[0]
        options, data = gnr.parse_line(line)
        data = gnr.generate_barcode_data(barcode_type, 50)

        if barcode_type and data:
            with open("/home/ilya/barcode_generator/config.yaml", "r") as yaml_file:
                config = yaml.safe_load(yaml_file)

            config["barcode_type"] = barcode_type
            config["options"] = gnr.format_options(options)

            with open("/home/ilya/barcode_generator/config.yaml", "w") as yaml_file:
                yaml.dump(config, yaml_file, Dumper=gnr.Dumper)

            with open("/home/ilya/barcode_generator/input.csv", "w") as csv_file:
                for item in data:
                    if knowledge_base.validate_barcode(barcode_type, item):
                        csv_file.write(f"{item}\n")
                    else:
                        raise Exception("Wrong data!")

            try:
                subprocess.run(["/home/ilya/barcode_generator/./start.sh", barcode_type])
            except Exception as e:
                print(e)

            annotation_path = os.path.join("all_outputs", f"{barcode_type}_annotation")
            template_path = "template.json"

            gnr.generate_annotations(value[1], annotation_path, f"all_outputs/{barcode_type}", template_path)

def make_transformation(image, annotation, barcode_type, type_transform):
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
        transformed_image, transformed_coords = snt.rotate(36)
        new_name += "_rotated.png"
    if type_transform == "down_view":
        dst_points = [(-width * 0.3, 0), (width * 1.3, 0), (width, height), (0, height)]
        transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
        new_name += "_perspective.png"
    if type_transform == "top_view":
        dst_points = [(0, 0), (width, 0), (width * 1.3, height), (-width * 0.3, height)]
        transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
        new_name += "_perspective.png"
    if type_transform == "left_view":
        dst_points = [(0, 0), (width, -height * 0.3), (width, height * 1.3), (0, height)]
        transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
        new_name += "_perspective.png"
    if type_transform == "right_view":
        dst_points = [(0, -height * 0.3), (width, 0), (width, height), (0, 1.3 * height)]
        transformed_image, transformed_coords = snt.change_perspective(orig_points, dst_points)
        new_name  += "_perspective.png"
    if type_transform == "noise":
        transformed_image, transformed_coords = snt.add_noise(200)
        new_name += "_noised.png"
    if type_transform == "zoom":
        transformed_image, transformed_coords = snt.zoom()
        new_name += "_scaled.png"
    if type_transform == "blur":
        transformed_image, transformed_coords = snt.add_blur()
        new_name += "_blured.png"
    if type_transform == "texture":
        transformed_image, transformed_coords = snt.add_texture("crumpled_paper.jpeg")
        new_name = "_textured.png"
    if type_transform == "glare":
        transformed_image, transformed_coords = snt.add_glare()
        new_name += "_with_glare.png"
    if type_transform == "brightness":
        transformed_image, transformed_coords = snt.adjust_brightness()
        new_name += "_brightness.png"
    if type_transform == "contrast":
        transformed_image, transformed_coords = snt.adjust_contrast()
        new_name += "_contrast.png"
    if type_transform == "saturation":
        transformed_image, transformed_coords = snt.adjust_saturation()
        new_name += "_saturation.png"

    if transformed_image and transformed_coords:
        transformed_image.save(file_path_to_save + new_name, format="PNG", optimize=True)
        shutil.move(transformed_coords, os.path.join(ann_path_to_save, transformed_coords))
    else:
        print("Не было выполнено преобразований")




if __name__ == "__main__":
    #generate_images_and_annotations()
    transformations = {"rotate": "rotate", "top_view": "top_view", "down_view": "down_view", "right_view": "right_view",
                       "left_view": "left_view", "noise": "noise", "zoom": "zoom", "blur": "blur", "texture": "texture",
                       "glare": "glare", "brightness": "brightness", "contrast": "contrast", "saturation": "saturation"}
    barcode_type = "code39"
    barcode_path = f"all_outputs/{barcode_type}"
    ann_path = f"all_outputs/{barcode_type}_annotation/"
    for filename in os.listdir(barcode_path):
        for type_transform in transformations.values():
            if os.path.splitext(filename)[1] != ".pdf":
                annotation = ann_path + os.path.splitext(filename)[0] + ".json"
                make_transformation(os.path.join(barcode_path, filename), annotation, barcode_type, type_transform)
        break