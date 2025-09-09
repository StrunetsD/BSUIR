from PIL import Image, ImageDraw


def med(image, x, y, z):
    pix = image.load()
    window_values = []
    for i in range(-1, 2):
        for j in range(-1, 2):
            if (x+i >= 0) and (y+j >= 0) and (x+i < image.size[0]) and (y+j < image.size[1]):
                window_values.append(pix[x+i, y+j][z])
    window_values.sort()
    return window_values[3]  # медианное значение


image = Image.open(r"../images/image2.jpg")
new = Image.new("RGB", image.size)
draw = ImageDraw.Draw(new)


for i in range(image.size[0]):
    for j in range(image.size[1]):
        a = med(image, i, j, 0)
        b = med(image, i, j, 1)
        c = med(image, i, j, 2)
        draw.point((i, j), (a, b, c))

new.save(r"images\new_image.jpg", "JPEG")