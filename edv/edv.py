# Copyright (c) 2024 Jan Tünnermann. All rights reserved.
# This work is licensed under the terms of the MIT license.  
# For a copy, see <https://opensource.org/licenses/MIT>
# or the LICENSE file in the repository that hosts this software

import argparse
import importlib.resources as pkg_resources
import yaml
import numpy as np
from os import path
from PIL import Image, ImageEnhance
import requests

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
    parser.add_argument("-t", "--template",
        help="Template to be used")
    parser.add_argument("-d", "--display",
        help="Display to be transformed onto the base image")
    parser.add_argument("-b", "--brightness",
        help="Brightness adjustment; 0 is full black, values larger than one increase brightness")
    parser.add_argument("-o", "--out",
        help="Output filename; if not provided, 'Figure_' will be appended to the display filename")
    parser.add_argument("-s", "--show", action="store_true",
        help="If provided, image is shown and not saved!")

    args = parser.parse_args()

    if args.out is None:
        args.out = "Figure_" + args.display

    # Load the user-provided display
    display_img = Image.open(args.display).convert("RGBA")

    # Adjust brightness if provided
    if args.brightness:
        bf = ImageEnhance.Brightness(display_img)
        display_img = bf.enhance(float(args.brightness))

    # Load base image from template
    with pkg_resources.path('edv.templates.'+ args.template, "base.png") as base_path:
        base_img = Image.open(base_path).convert("RGBA")

    # Load the mask if the template has one
    with pkg_resources.path('edv.templates.'+ args.template, "mask.png") as mask_path:
        if path.exists(mask_path):
            mask = Image.open(path.join("templates", args.template, "mask.png")).convert("L")
        else:
            mask = Image.new("L", base_img.size, 255)

    # Load coordinates from template
    with pkg_resources.path('edv.templates.'+ args.template, "coords.yml") as coords_path:
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