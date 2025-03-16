import numpy as np
from tqdm import tqdm

class Dither:
	def __init__(
			self,
			mode="FloydSteinberg",
			colour_space="srgb",
		):
		self.mode = mode # "FloydSteinberg" or "Atkinson"
		self.colour_space = colour_space

		# Perceptual luminance coefficients for lin-srgb
		self.perceptual_luminance_rgb = np.array([0.2126, 0.7152, 0.0722])  # R, G, B perception weights
		return
	
	# Convert the image from sRGB into a linear colour-space
	# sRGB "gamma" function (approx 2.2)
	# Based on https://stackoverflow.com/questions/596216/formula-to-determine-perceived-brightness-of-rgb-color/13558570#13558570
	def gam_sRGB(self, c):
		return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)

	# De-linearise the image into sRGB again
	def inv_gam_sRGB(self, c):
		return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1.0 / 2.4) - 0.055)
	
	def linsrgb_to_oklab(self, c):
		l = 0.4122214708 * c[0] + 0.5363325363 * c[1] + 0.0514459929 * c[2]
		m = 0.2119034982 * c[0] + 0.6806995451 * c[1] + 0.1073969566 * c[2]
		s = 0.0883024619 * c[0] + 0.2817188376 * c[1] + 0.6299787005 * c[2]

		l_ = np.cbrt(l)
		m_ = np.cbrt(m)
		s_ = np.cbrt(s)

		return np.array([
			0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
			1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
			0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_
		])
	
	def oklab_to_linsrgb(self, c):
		l_ = c[0] + 0.3963377774 * c[1] + 0.2158037573 * c[2]
		m_ = c[0] - 0.1055613458 * c[1] - 0.0638541728 * c[2]
		s_ = c[0] - 0.0894841775 * c[1] - 1.2914855480 * c[2]

		l = l_ ** 3
		m = m_ ** 3
		s = s_ ** 3

		return np.array([
			4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
			-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
			-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
		])
	
	# Convert the image from sRGB into OKLab
	def oklab(self, c):
		# Convert to linear sRGB
		c = self.gam_sRGB(c)
		return np.apply_along_axis(self.linsrgb_to_oklab, axis=2 if c.ndim == 3 else 1, arr=c)

	# Convert from OKLab into sRGB
	def inv_oklab(self, c):
		c = np.apply_along_axis(self.oklab_to_linsrgb, axis=2 if c.ndim == 3 else 1, arr=c)
		# Clip values
		c = np.clip(c, 0, 1)

		# De-linearise sRGB
		return self.inv_gam_sRGB(c)
	
	def apply_colour_space(self, values, colour_space="srgb"):
		# if the colour space is srgb, don't do anything
		if colour_space == "srgb":
			return values
		if colour_space == "lin-srgb":
			return self.gam_sRGB(values)
		if colour_space == "oklab":
			return self.oklab(values)

		raise Exception(f"Unimplemented colour space: {colour_space}")
	
	def unapply_colour_space(self, values, colour_space="srgb"):
		# if the colour space is srgb, don't do anything
		if colour_space == "srgb":
			return values
		if colour_space == "lin-srgb":
			return self.inv_gam_sRGB(values)
		if colour_space == "oklab":
			return self.inv_oklab(values)

		raise Exception(f"Unimplemented colour space: {colour_space}")
		
	def __dither(self, image, palette):
		y_max, x_max, _ = image.shape

		for y in tqdm(range(y_max), unit="rows"):
			for x in range(x_max):
				# Calculate differences between pixel and palettes
				diffs = palette - image[y, x]

				# Weight differences in linear sRGB
				if self.colour_space == "lin-srgb":
					diffs = diffs * self.perceptual_luminance_rgb

				# Skip sqrt for speed when calculating euclidean distance
				dists_sq = np.sum(diffs * diffs, axis=1)
				index = np.argmin(dists_sq)

				# Calculate error for diffusion
				error = image[y, x] - palette[index]

				# Set pixel to closest color
				image[y, x] = palette[index]

				if self.mode == "FloydSteinberg":
					# Floyd-Steinberg Dithering
					if x + 1 < x_max:
						image[y, x+1] += error * 7 / 16
					if y + 1 < y_max:
						if x - 1 >= 0:
							image[y+1, x-1] += error * 3 / 16
						image[y+1, x] += error * 5 / 16
						if x + 1 < x_max:
							image[y+1, x+1] += error * 1 / 16
				elif self.mode == "Atkinson":
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

		image_converted = self.apply_colour_space(image, self.colour_space)
		palette_converted = self.apply_colour_space(palette, self.colour_space)

		dithered = self.__dither(image_converted, palette_converted)

		dithered_srgb = self.unapply_colour_space(dithered, self.colour_space)

		# Quantise image back to 0..255 values for displaying
		return (dithered_srgb * 255).astype(np.uint8)