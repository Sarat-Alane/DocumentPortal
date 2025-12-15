# /root/backend/python-service/src/services/ocr_service/ocr_module.py

# This module contains code to extract text from the images one by one and append it to the output.txt file

import os
from datetime import datetime
from paddleocr import PaddleOCR
from PIL import Image

def extract_text_from_image(ocr, image_path, output_file='extracted_text.txt'):
    try:
        if not os.path.exists(image_path):
            print(f"Error: Image file '{image_path}' not found!")
            return

        print(f"Processing image: {image_path}")
        
        # 🔧 PRE-FIX: Ensure image is within safe size and RGB format
        img = Image.open(image_path)
        img = img.convert("RGB")  # removes alpha channel if present

        max_side_limit = 3000  # safe limit
        w, h = img.size
        if max(w, h) > max_side_limit:
            scale = max_side_limit / max(w, h)
            new_size = (int(w * scale), int(h * scale))
            print(f"Resizing image from {img.size} to {new_size}")
            img = img.resize(new_size, Image.LANCZOS)
            img.save(image_path)

        result = ocr.predict(image_path)
        extracted_text = []

        if result and len(result) > 0:
            for line in result:
                try:
                    if isinstance(line, list) and len(line) >= 2:
                        if isinstance(line[1], list) and len(line[1]) >= 2:
                            text = line[1][0]
                            confidence = line[1][1]
                        elif isinstance(line[1], str):
                            text = line[1]
                            confidence = 1.0
                        else:
                            text = str(line[1])
                            confidence = 1.0
                    elif isinstance(line, tuple) and len(line) >= 2:
                        text = line[1]
                        confidence = 1.0
                    else:
                        text = str(line)
                        confidence = 1.0

                    extracted_text.append(f"{text} (confidence: {confidence:.2f})")
                except Exception as e:
                    print(f"Error processing line {line}: {e}")
                    extracted_text.append(f"Error processing line: {str(line)}")

        out_dir = os.path.dirname(output_file)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)

        with open(output_file, 'a', encoding='utf-8') as f:
            f.write("\n" + "=" * 70 + "\n")
            f.write(f"Text extracted from: {image_path}\n")
            f.write(f"Extraction time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("-" * 50 + "\n\n")

            if extracted_text:
                for text in extracted_text:
                    f.write(text + "\n")
            else:
                f.write("No text found in the image.\n")

        print(f"Text extraction completed for {image_path}")
        return result

    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None
