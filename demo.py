from ditherpy import Dither
from PIL import Image
import numpy as np

# Test image using Dürer's Young Hare
input_image = Image.open("hare-input.jpg").convert("RGB")
# Test image using an RGB gradient
input_gradient = Image.open("gradient-input.png").convert("RGB")
# Test image using a BW gradient
input_gradient_bw = Image.open("gradient-bw-input.png").convert("RGB")

ditherer_linear = Dither(mode="FloydSteinberg", linearise=True, correct_perception=True)
ditherer_sRGB = Dither(mode="FloydSteinberg", linearise=False, correct_perception=False)

# RGB palette
palette_rgb = np.array([[0, 0, 0], [255, 255, 255], [255, 0, 0], [0, 255, 0], [0, 0, 255]])
palette_bw = np.array([[0, 0, 0], [255, 255, 255]])

# Dither all images
for name, img, palette in [
	("hare", input_image, palette_rgb), 
	("gradient", input_gradient, palette_rgb), 
	("gradient-bw", input_gradient_bw, palette_bw)
]:
	print(f"Dithering {name} :")

	# Linearise and dither
	print(f"Dithering in linear colour-space...")
	dithered_linear = ditherer_linear.dither(img, palette)

	# Dither directly in sRGB
	print(f"Dithering in sRGB colour-space...")
	dithered_sRGB = ditherer_sRGB.dither(img, palette)

	if dithered_sRGB.shape[0] >= dithered_sRGB.shape[1]:
		concat_axis = 1
	else:
		concat_axis = 0

	# Write images to file
	output = Image.fromarray(np.concatenate([
			img,
			dithered_linear,
			dithered_sRGB
	], axis=concat_axis))
	output.save(f"{name}.png")
	print(f"Saved {name}.png to file.\n")
