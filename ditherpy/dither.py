import numpy as np
from tqdm import tqdm

class Dither:
	def __init__(
			self,
			linearise=True,
			correct_perception=True
		):
		self.linearise = linearise # Linearise the image's colours before

		self.correct_perception = correct_perception # Correct for perception when comparing colors
		self.weights = np.array([0.2126, 0.7152, 0.0722])  # R, G, B perception weights
		return
	
	# Convert the image from sRGB into a linear colour-space
	# sRGB "gamma" function (approx 2.2)
	# Based on https://stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color/13558570#13558570
	def gam_sRGB(self, c):
		return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

	# De-linearise the image into sRGB again
	def inv_gam_sRGB(self, v):
		return np.where(v <= 0.0031308, v * 12.92, 1.055 * np.power(v, 1.0 / 2.4) - 0.055)
		
	def __dither(self, image, palette):
		y_max, x_max, _ = image.shape

		for y in tqdm(range(y_max), unit="rows"):
			for x in range(x_max):
				# Calculate differences between pixel and palettes
				diffs = palette - image[y, x]

				# Weight differences
				if self.correct_perception:
					diffs = diffs * self.weights

				# Skip sqrt for speed when calculating euclidean distance
				dists_sq = np.sum(diffs * diffs, axis=1)
				index = np.argmin(dists_sq)

				# Calculate error for diffusion
				error = image[y, x] - palette[index]

				# Set pixel to closest color
				image[y, x] = palette[index]

				# Atkinson Dithering
				if x + 1 < x_max:
					image[y, x+1] += error / 8
				if x + 2 < x_max:
					image[y, x+2] += error / 8
				if y + 1 < y_max:
					if x - 1 >= 0:
						image[y+1, x-1] += error / 8
					image[y+1, x] += error / 8
					if x + 1 < x_max:
						image[y+1, x+1] += error / 8
				if y + 2 < y_max:
					image[y+2, x] += error / 8

		return image
	
	def dither(self, image, palette=np.array([[0, 0, 0], [255, 255, 255]])):
		image = np.array(image)

		# Scale to float32 0..1
		if np.max(image) > 1.0:
			image = image.astype(np.float32) / 255
		if np.max(palette) > 1.0:
			palette = palette.astype(np.float32) / 255

		if self.linearise:
			image = self.gam_sRGB(image)
			palette = self.gam_sRGB(palette)

		dithered = self.__dither(image, palette)

		if self.linearise:
			dithered = self.inv_gam_sRGB(dithered)

		# Quantise image back to 0..255 values for displaying
		return (dithered * 255).astype(np.uint8)