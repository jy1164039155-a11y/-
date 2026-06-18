import os
from PIL import Image

def main():
    img1_path = "d:/评估报告工具/temp_design/image1.jpg"
    img2_path = "d:/评估报告工具/temp_design/image2.jpg"
    
    if os.path.exists(img1_path):
        with Image.open(img1_path) as img1:
            print(f"Image 1 size: {img1.size}, format: {img1.format}")
    else:
        print("Image 1 not found")
        
    if os.path.exists(img2_path):
        with Image.open(img2_path) as img2:
            print(f"Image 2 size: {img2.size}, format: {img2.format}")
    else:
        print("Image 2 not found")

if __name__ == "__main__":
    main()
