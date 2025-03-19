from ditherpy import Dither
from PIL import Image
import numpy as np

# Test image using Dürer's Young Hare
input_image = Image.open("hare-input.jpg").convert("RGB")
# Test image using an RGB gradient
input_gradient = Image.open("gradient-input.png").convert("RGB")
# Test image using a BW gradient
input_gradient_bw = Image.open("gradient-bw-input.png").convert("RGB")

ditherer1 = Dither(mode="FloydSteinberg", colour_space="oklab")
ditherer2 = Dither(mode="FloydSteinberg", colour_space="lin-srgb")

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
	print(f"Dithering in {ditherer1.colour_space} colour-space, using {ditherer1.mode}...")
	dithered_linear = ditherer1.dither(img, palette)

	# Dither directly in sRGB
	print(f"Dithering in {ditherer2.colour_space} colour-space, using {ditherer2.mode}..")
	dithered_sRGB = ditherer2.dither(img, palette)

	# Select horizontal or vertical grid for the output based on aspect ratio
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
