#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo

from vector_math import VectorMath

# =============

# Create a GTK+ widget on which we will draw using Cairo
class CairoUtils(VectorMath):

	# -------------

	def determine_drawing_boundaries(self, point_array):

		ordinates = [x for (x,y) in point_array]
		abscissas = [y for (x,y) in point_array]
		self.upper_left = ( min(ordinates), min(abscissas) )
		self.lower_right = ( max(ordinates), max(abscissas) )
		self.original_width, self.original_height = self.displacement(self.upper_left, self.lower_right)

	# -------------

	def color_with_alpha(self, cairo_context, color_string, alpha_value):

		if color_string is "gray":
			cairo_context.set_source_rgba(0.6, 0.6, 0.6, alpha_value)
			return

		try:
#			print "tried parsing", color_string
			original_color = gtk.gdk.color_parse(color_string)
		except ValueError:
			print "\"" + color_string + "\" is an invalid color."
			original_color = gtk.gdk.color_parse("magenta")

		cairo_context.set_source_rgba(original_color.red, original_color.green, original_color.blue, alpha_value)


	# -------------

	def save_image_to_file(self, filename, img_width=300, img_height=300, raster=True):

		if raster:
			img = cairo.ImageSurface(cairo.FORMAT_ARGB32, img_width, img_height)
			width, height = img.get_width(), img.get_height()
			c = cairo.Context(img)
			self.draw(c, width, height)
			img.write_to_png(filename + ".png")
		else:
			surf = cairo.PDFSurface(filename + ".pdf", img_width, img_height)
			cr = cairo.Context(surf)
			self.draw(cr, img_width, img_height)
			cr.show_page()

		print "Wrote", filename, "at", img_width, "by", img_height, "pixels."

