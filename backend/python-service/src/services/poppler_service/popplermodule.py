# /root/backend/python-service/src/services/poppler_services/popplermodule.py

# This module contains the function to convert the PDFs to image and store them in the /images folder as well as cleanup the /images folder after processing the PDFs

from pdf2image import convert_from_path
import os




def pdf_to_images_function(pdf_path, output_folder, poppler_path=r"C:\poppler-24.08.0\Library\bin", dpi=200, image_format='png'):
    os.makedirs(output_folder, exist_ok=True)
    print(f"Converting '{pdf_path}' to images...")

    pages = convert_from_path(pdf_path, dpi=dpi, poppler_path=poppler_path)

    image_paths = []
    for idx, page in enumerate(pages, start=1):
        image_filename = os.path.join(output_folder, f"page_{idx}.{image_format}")
        page.save(image_filename, image_format.upper())
        image_paths.append(image_filename)
        print(f"Saved: {image_filename}")

    print(f"PDF successfully converted! Images saved in: {output_folder}")
    return image_paths