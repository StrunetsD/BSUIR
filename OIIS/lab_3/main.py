from PIL import Image

image_one = Image.open('../images/lab_3_1.jpg')
image_two = Image.open('../images/lab_3_2.jpg')

image_one_pixels = list(image_one.getdata())
image_one_mean_brightness = sum(pixel[0] + pixel[1] + pixel[2] for pixel in image_one_pixels) / (len(image_one_pixels) * 3) # среднее з-е яркости 

image_two_pixels = list(image_two.getdata())
image_two_mean_brightness = sum(pixel[0] + pixel[1] + pixel[2] for pixel in image_two_pixels) / (len(image_two_pixels) * 3)

brightness_diff = abs(image_one_mean_brightness - image_two_mean_brightness) / 2

if image_one_mean_brightness > image_two_mean_brightness:
    new_image_one_pixels = [(max(0, int(pixel[0] - brightness_diff)),
                             max(0, int(pixel[1] - brightness_diff)),
                             max(0, int(pixel[2] - brightness_diff))) for pixel in image_one_pixels]

    new_image_two_pixels = [(min(255, int(pixel[0] + brightness_diff)),
                             min(255, int(pixel[1] + brightness_diff)),
                             min(255, int(pixel[2] + brightness_diff))) for pixel in image_two_pixels]
else:
    new_image_one_pixels = [(min(255, int(pixel[0] + brightness_diff)),
                             min(255, int(pixel[1] + brightness_diff)),
                             min(255, int(pixel[2] + brightness_diff))) for pixel in image_one_pixels]

    new_image_two_pixels = [(max(0, int(pixel[0] - brightness_diff)),
                             max(0, int(pixel[1] - brightness_diff)),
                             max(0, int(pixel[2] - brightness_diff))) for pixel in image_two_pixels]

image_one_width, image_one_height = image_one.size
image_two_width, image_two_height = image_two.size

new_image_one = Image.new('RGB', (image_one_width, image_one_height))
new_image_one.putdata(new_image_one_pixels)
new_image_two = Image.new('RGB', (image_two_width, image_two_height))
new_image_two.putdata(new_image_two_pixels)

new_image_one.save('result_image_1.jpg')
new_image_two.save('result_image_2.jpg')