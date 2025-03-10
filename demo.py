from ditherpy import Dither
from PIL import Image
import numpy as np

# Test image using Dürer's Young Hare
input_image = Image.open("hare-input.jpg").convert("RGB")
# Test image using an RGB gradient
input_gradient = Image.open("gradient-input.png").convert("RGB")

ditherer_linear = Dither()
ditherer_sRGB = Dither(linearise=False, correct_perception=False)

# RGB palette
palette = np.array([[0, 0, 0], [255, 255, 255], [255, 0, 0], [0, 255, 0], [0, 0, 255]])

# Dither all images
for name, img in [("hare", input_image), ("gradient", input_gradient)]:
	print(f"Dithering {name} :")

	# Linearise and dither
	print(f"Dithering in linear colour-space...")
	dithered_linear = Dither().dither(img, palette)

	# Dither directly in sRGB
	print(f"Dithering in sRGB colour-space...")
	dithered_sRGB = Dither(
		linearise=False,
		correct_perception=False
	).dither(img, palette)

	# Write images to file
	output = Image.fromarray(np.concatenate([
			img,
			dithered_linear,
			dithered_sRGB
	], axis=1))
	output.save(f"{name}.png")
	print(f"Saved {name}.png to file.\n")
