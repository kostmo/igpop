#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, gobject, cairo



# =============

# Create a GTK+ widget on which we will draw using Cairo
class Screen(gtk.DrawingArea):


	def __init__(self, parent_window, num_points = 4):
		gtk.DrawingArea.__init__(self)

		self.parent_window = parent_window

		self.steering_coords = (0, 0)	# For Pointer Motion


#		self.connect("motion_notify_event", self.motion_notify_event)
		self.connect("button_press_event", self.button_press_event)

		self.set_events(gtk.gdk.EXPOSURE_MASK			# are each of these MASKS necessary?
						| gtk.gdk.LEAVE_NOTIFY_MASK
						| gtk.gdk.BUTTON_PRESS_MASK
						| gtk.gdk.POINTER_MOTION_MASK
						| gtk.gdk.POINTER_MOTION_HINT_MASK)


		self.border_padding = 5
		self.stroke_width = 0.01

		from random import randint

		self.my_points = self.gen_points( randint(2, num_points) )
		self.my_controls = self.gen_points( len(self.my_points) )

#		self.modify_base_control_points()
		self.generate_smooth_control_points()
		self.determine_drawing_boundaries()




		x_window, y_window = self.vector_scale(self.displacement(self.upper_left, self.lower_right), 100)
		self.window_scale = int(x_window), int(y_window)


		self.animation_transition_countdown = None
		self.animation_transition_steps = 100



	# -------------

	def trigonometric_interpolation(self, fraction):
		from math import cos, pi
		return (1 - cos(pi * fraction)) / 2.0

	# -------------

	def linear_interpolation(self, start_point, end_point, fraction):

		fraction = 	self.trigonometric_interpolation(fraction)	# COOL

		x_0, y_0 = start_point
		x_1, y_1 = end_point

		x_interp = x_0 + fraction*(x_1 - x_0)
		y_interp = y_0 + fraction*(y_1 - y_0)

		return (x_interp, y_interp)

	# -------------

	def color_with_alpha(self, cairo_context, color_string, alpha_value):

		try:
			original_color = gtk.gdk.color_parse(color_string)
		except ValueError:
			print "\"" + color_string + "\" is an invalid color."
			original_color = gtk.gdk.color_parse("gray")

		cairo_context.set_source_rgba(original_color.red, original_color.green, original_color.blue, alpha_value)

	# -------------

	def draw_simple_circle(self, cr, coord_pair, color = "blue", radius = None):


		if radius is None:
			radius = self.stroke_width

		from math import pi
		pos_x, pos_y = coord_pair

		self.color_with_alpha(cr, color, 0.5)
		cr.arc( pos_x, pos_y, radius, 0, 2 * pi)
		cr.stroke()

	# -------------

	def gen_points(self, num_points):
		points = []
		from random import random
		for i in range(num_points):
			points.append( (random(), random()) )
		return points

	# -------------


	def modify_base_control_points(self):
		self.my_controls = []
		for point in self.primary_control_points:
			mod_point = self.vector_add(point, self.steering_coords)
			self.my_controls.append( mod_point )


	# -------------

	def determine_drawing_boundaries(self):
		mixed_ctrl_points = self.smooth_takeoff + self.my_controls
		ordinates = [x for (x,y) in mixed_ctrl_points]
		abscissas = [y for (x,y) in mixed_ctrl_points]
		self.upper_left = ( min(ordinates), min(abscissas) )
		self.lower_right = ( max(ordinates), max(abscissas) )
		self.original_width, self.original_height = self.displacement(self.upper_left, self.lower_right)

	# -------------

	def generate_smooth_control_points(self):

		self.smooth_takeoff = []
		for i in range(len(self.my_points)):
			last_ctrl_point = self.my_controls[i - 1]
			last_path_point = self.my_points[i - 1]
			self.smooth_takeoff.append( self.vector_add( self.displacement(last_ctrl_point, last_path_point), last_path_point) )

	# -------------

	def transition_timeout_function(self):

		if self.animation_transition_countdown > 0:
			self.animation_transition_countdown -= 1
			path_fraction = 1.0 * (self.animation_transition_steps - self.animation_transition_countdown) / self.animation_transition_steps

			self.my_points = []
			self.my_controls = []
			for i in range(len(self.old_path_point_backup)):
				interp_path_pt = self.linear_interpolation(self.old_path_point_backup[i], self.new_path_point_backup[i], path_fraction)
				self.my_points.append(interp_path_pt)
				interp_control_pt = self.linear_interpolation(self.old_control_point_backup[i], self.new_control_point_backup[i], path_fraction)
				self.my_controls.append(interp_control_pt)

			self.generate_smooth_control_points()
			self.queue_draw()
			return True

		else:
			self.my_points = self.new_path_point_backup
			self.my_controls = self.new_control_point_backup
			self.generate_smooth_control_points()
			self.initialize_animation_transition()	# FUN
			return False

	# -------------

	def initialize_animation_transition(self):

		self.old_path_point_backup = self.my_points[:]
		self.old_control_point_backup = self.my_controls[:]

		self.my_points = self.gen_points( len(self.my_points) )
		self.my_controls = self.gen_points( len(self.my_points) )

		self.new_path_point_backup = self.my_points[:]
		self.new_control_point_backup = self.my_controls[:]

		self.animation_transition_countdown = self.animation_transition_steps
		from gobject import timeout_add
		timeout_add(60, self.transition_timeout_function)


	# -------------

	def button_press_event(self, widget, event):

		if event.button == 1 and not self.animation_transition_countdown:

			self.initialize_animation_transition()

		elif event.button == 3:

			self.parent_window.remove(self)
			display_artwork(self.parent_window)



		return True








	# -------------

	def motion_notify_event(self, widget, event):
		if event.is_hint:
			x, y, state = event.window.get_pointer()
		else:
			x = event.x
			y = event.y
			state = event.state	# Unnecessary, for now

#		if state & gtk.gdk.BUTTON1_MASK:

		widget.queue_draw()
		x_off, y_off = self.window.get_size()

		corrected_x, corrected_y = x - x_off/2.0, y - y_off/2.0
		unit_radius = 2.0
		self.steering_coords =  corrected_x / (x_off/unit_radius), corrected_y / (y_off/unit_radius)




#		self.modify_base_control_points()
		self.generate_smooth_control_points()
#		self.determine_drawing_boundaries()	# EXPERIMENTAL, REQUIRES CENTERING TO LOOK GOOD



		return True

	# -------------

	# Draw in response to an expose-event
	__gsignals__ = { "expose-event": "override" }

	# -------------

	def mag(self, vector):
		x, y = vector
		from math import sqrt
		return sqrt(x**2 + y**2)

	# -------------

	def displacement(self, start_point, end_point):
		x1, y1 = start_point
		x2, y2 = end_point
		return (x2 - x1, y2 - y1)

	# -------------

	def vector_scale(self, vector, scalar):
		x, y = vector
		return (x*scalar, y*scalar)

	# -------------

	def vector_add(self, first_point, second_point):
		x1, y1 = first_point
		x2, y2 = second_point
		return (x1 + x2, y1 + y2)

	# -------------

	# Handle the expose-event by drawing
	def do_expose_event(self, event):

		# Create the cairo context
		cr = self.window.cairo_create()

		# Restrict Cairo to the exposed area; avoid extra work
		cr.rectangle(event.area.x, event.area.y,
		        event.area.width, event.area.height)
		cr.clip()

		self.draw(cr, *self.window.get_size())

	# -------------

	def draw(self, cr, width, height):

		potential_w_scale = (width - 2*self.border_padding) / self.original_width
		potential_h_scale = (height - 2*self.border_padding) / self.original_height
		draw_scale = min(potential_w_scale, potential_h_scale)


		cr.translate((width - draw_scale*self.original_width)/2.0, (height - draw_scale*self.original_height)/2.0)
		cr.scale(draw_scale, draw_scale)
		cr.translate( *self.vector_scale(self.upper_left, -1) )


		cr.set_line_width(self.stroke_width)
		self.color_with_alpha(cr, "blue", 0.8)
		cr.move_to(*self.my_points[-1])
		for i in range(len(self.my_points)):
			takeoff_x, takeoff_y = self.smooth_takeoff[i]
			approach_x, approach_y = self.my_controls[i]
			cr.curve_to(takeoff_x, takeoff_y, approach_x, approach_y, *self.my_points[i])
		cr.stroke()
#		cr.fill()


		for point in self.my_points:
			self.draw_simple_circle(cr, point, "black", radius = self.stroke_width*3)


		self.color_with_alpha(cr, "black", 1.0)
		ul_x, ul_y = self.upper_left

		cr.rectangle(ul_x, ul_y, *self.displacement(self.upper_left, self.lower_right))
		cr.stroke()



		if True:

			for i in range(len(self.my_points)):

				# Control point
				self.draw_simple_circle(cr, self.my_controls[i], "red")

				# Mirrored control point
				next_point_x, next_point_y = self.my_points[i]
				takeoff_x, takeoff_y = self.displacement(self.my_controls[i], self.my_points[i])
				new_takeoff = next_point_x + takeoff_x, next_point_y + takeoff_y
				self.draw_simple_circle(cr, new_takeoff, "magenta")

				cr.set_dash([self.stroke_width*2])
				# Arrival Vector
				self.color_with_alpha(cr, "green", 0.5)
				cr.move_to(*self.my_points[i])
				cr.line_to(*self.my_controls[i])
				cr.stroke()

				# Departure Vector
				self.color_with_alpha(cr, "black", 0.5)
				cr.move_to(*self.my_points[i])
				cr.line_to(*new_takeoff)
				cr.stroke()

				cr.set_dash([])




# =============

# GTK mumbo-jumbo to show the widget in a window and quit when it's closed
def run():

	window = gtk.Window()
	window.connect("delete-event", gtk.main_quit)


	display_artwork(window)


	window.present()
	gtk.main()

# =============

def display_artwork(window):
	widget = Screen(window, 7)
	widget.show()
	window.add(widget)
	window.set_size_request(*widget.window_scale)

# =============

if __name__ == "__main__":
	run()
