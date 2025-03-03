# Copyright (c) 2024, 2025 Jan Tünnermann. All rights reserved.
# This work is licensed under the terms of the MIT license.  
# For a copy, see <https://opensource.org/licenses/MIT>
# or the LICENSE file in the repository that hosts this software

import argparse
import importlib.resources as pkg_resources
import yaml
import numpy as np
from os import path, makedirs
from PIL import Image, ImageEnhance
import requests
from zipfile import ZipFile, BadZipFile
from io import BytesIO

TEMPLATE_ARCHIVE = "https://raw.githubusercontent.com/jt-lab/edv/refs/heads/main/templates.zip"


def download_and_extract_zip(url, destination):
    try:
        print(f"Downloading templates from {url}...")
        response = requests.get(url)
        response.raise_for_status()

        with ZipFile(BytesIO(response.content)) as zip_file:
            zip_file.extractall(destination)
            print(f"Templates successfully downloaded and extracted to: {destination}")

    except requests.RequestException as e:
        print(f"Failed to download the zip file: {e}")
    except BadZipFile as e:
        print(f"Failed to extract the zip file: {e}")

def find_coeffs(source_coords, target_coords):
    # Based on: https://stackoverflow.com/questions/53032270/perspective-transform-with-python-pil-using-src-target-coordinates
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    A = np.matrix(matrix, dtype=float)
    B = np.array(source_coords).reshape(8)
    res = np.dot(np.linalg.inv(A.T * A) * A.T, B)
    return np.array(res).reshape(8)

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-t", "--template", required=True,
        help="Template to be used")
    parser.add_argument("-d", "--display",required=True,
        help="Display to be transformed onto the base image")
    parser.add_argument("-b", "--brightness",
        help="Brightness adjustment; 0 is full black, values larger than one increase brightness")
    parser.add_argument("-o", "--out",
        help="Output filename; if not provided, 'Figure_' will be appended to the display filename")
    parser.add_argument("-s", "--show", action="store_true",
        help="If provided, image is shown and not saved!")

    try:
        args = parser.parse_args()
    except SystemExit as e:
            return

    if args.out is None:
        args.out = "Figure_" + path.basename(args.display)

    # Check if template folder exists
    template_folder = path.join(path.expanduser("~"), "edv_templates")

    if not path.exists(template_folder):
        while True:
            response = input("No template directory '~/edv_templates' detected. Create the directory and download templates? [y/n]: ").strip().lower()
            if response in {'y', 'n'}:
                break
        if response == 'y':
               makedirs(template_folder)
               download_and_extract_zip(TEMPLATE_ARCHIVE, template_folder)
    
    # Load the user-provided display
    display_img = Image.open(args.display).convert("RGBA")

    # Adjust brightness if provided
    if args.brightness:
        bf = ImageEnhance.Brightness(display_img)
        display_img = bf.enhance(float(args.brightness))

    # Load base image from template
    base_path = path.join(template_folder,  args.template, "base.png")
    base_img = Image.open(base_path).convert("RGBA")

    # Load the mask if the template has one
    mask_path = path.join(template_folder, args.template, "mask.png")
    if path.exists(mask_path):
        mask = Image.open(path.join(template_folder, args.template, "mask.png")).convert("L")
    else:
        mask = Image.new("L", base_img.size, 255)

    # Load coordinates from template
    coords_path = path.join(template_folder, args.template, "coords.yml")
    with open(coords_path, "r") as file:
        coords = yaml.safe_load(file)

    # Source coords cover the whole display image
    source_coords = [[0, 0], [display_img.width, 0],
                     [display_img.width, display_img.height], [0, display_img.height]]

    # Target coords from the template yaml file
    target_coords = [coords["upper_left"], coords["upper_right"],
                     coords["lower_right"], coords["lower_left"]]

    # Compute transformation coefficients
    coeffs = find_coeffs(source_coords, target_coords)

    # Compute and apply perspective transform
    transformed_display_img = display_img.transform(
        base_img.size, Image.Transform.PERSPECTIVE, coeffs, resample=Image.BICUBIC
    )

    # Paste the transformed display onto the base image
    base_img.paste(transformed_display_img, (0, 0), mask)

    if args.show:
        base_img.show()
    else:
        base_img.save(args.out)

# Ensure main is called when the script is executed directly
if __name__ == "__main__":
    main()
