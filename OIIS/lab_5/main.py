from PIL import Image

def create_stereoscopic_image(left_image_path, right_image_path, output_path):
    left_image = Image.open(left_image_path).convert("RGB")
    right_image = Image.open(right_image_path).convert("RGB")

    if left_image.size != right_image.size:
        print("Image mast be same size")
        return

    left_r, _, _ = left_image.split()
    _, right_g, right_b = right_image.split()

    stereoscopic_image = Image.merge("RGB", (left_r, right_g, right_b))

    stereoscopic_image.save(output_path)
    print(f"Stereoscopic image save in {output_path}")

if __name__ == '__main__':
    left_image_path = "../images/image_5.png"
    right_image_path = "../images/image_5_1.png"
    output_path = "./stereoscopic_image.jpg"

    create_stereoscopic_image(left_image_path, right_image_path, output_path)
