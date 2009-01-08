#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, cairo

from datetime import datetime

from cairo_drawlib import CairoUtils
from pygraphviz import AGraph
# ==========================================================

class CairoGraph(gtk.DrawingArea, CairoUtils):

	message_colors = ["green", "red", "blue", "yellow", "black"]

	# Draw in response to an expose-event
	__gsignals__ = { "expose-event": "override" }

	# -------------

	# Handle the expose-event by drawing
	def do_expose_event(self, event):

		# Create the cairo context
		cr = self.window.cairo_create()

		# Restrict Cairo to the exposed area; avoid extra work
		cr.rectangle(event.area.x, event.area.y, event.area.width, event.area.height)
		cr.clip()

		self.draw(cr, *self.window.get_size())

	# -------------

	def __init__(self, gui_link):
		gtk.DrawingArea.__init__(self)


		self.gui_link = gui_link


		self.connect("motion_notify_event", self.motion_notify_event)
		self.connect("button_press_event", self.button_press_event)
		self.connect("leave_notify_event", self.leave_notify_event)

		self.set_events(  gtk.gdk.EXPOSURE_MASK
				| gtk.gdk.LEAVE_NOTIFY_MASK
				| gtk.gdk.BUTTON_PRESS_MASK
				| gtk.gdk.POINTER_MOTION_MASK
				| gtk.gdk.POINTER_MOTION_HINT_MASK)

		self.hover_selection = False

		self.dash_length = 6.0
		self.stroke_width = 2.0
		self.atom_radius = 15
		self.halo_radius = 2*self.atom_radius
		self.max_atom_padding = 2*self.halo_radius + self.stroke_width

		self.gui_active_node_id = None
		self.active_edge = None

		self.edge_adding_start_node = None

		self.last_mouse_coords = (0, 0)

	# -------------

	def regen_points(self, collection_reference):

		self.collection_reference = collection_reference

		graph_reference = collection_reference.B

		self.node_positions_by_label = {}
		self.node_colors_by_label = {}
		self.node_reference_by_label = {}

		for node in graph_reference.nodes():

			coords = node.attr['pos'].split(",")
			point = (int(coords[0]), -int(coords[1]))	# Inverts the y-axis

			self.node_positions_by_label[int(node)] = point
			self.node_colors_by_label[int(node)] = collection_reference.named_color[ self.collection_reference.get_atom_by_label( int(node) ).atom_type ]
			self.node_reference_by_label[int(node)] = self.collection_reference.get_atom_by_label( int(node) )

		self.determine_drawing_boundaries( self.node_positions_by_label.values() )

	# -------------

	def draw_timer(self, cr, coord_pair, radius, rgba, fraction, needle_color = "red"):

		from math import pi

		cr.save()
		cr.translate( *coord_pair )
		cr.rotate( -pi/2 )

		cr.move_to(0, 0)
		cr.rel_line_to(radius, 0)
		cr.arc(0, 0, radius, 0, -2*pi * (fraction) )
		cr.close_path()

		cr.set_source_rgba( *rgba )
		cr.fill()

		# Draw seconds hand
		if fraction and needle_color != None:
			cr.rotate( -2*pi * fraction )
			cr.move_to(0, 0)
			cr.rel_line_to(radius, 0)
			self.color_with_alpha(cr, needle_color, 0.25)
			cr.stroke()

		cr.restore()

	# -------------

	def draw_halo(self, cr, coord_pair, radius, rgba):

		from math import pi
		pos_x, pos_y = coord_pair


		cr.move_to(pos_x, pos_y)
		cr.rel_line_to(radius, 0)		
		cr.arc( pos_x, pos_y, radius, 0, 2*pi)
		cr.close_path()

		radial = cairo.RadialGradient(pos_x, pos_y, self.atom_radius, pos_x, pos_y, radius)
		radial.add_color_stop_rgba(0, *rgba)
		radial.add_color_stop_rgba(1, 1, 1, 1, 0)

		cr.set_source( radial )
		cr.fill()

	# -------------

	def draw_simple_circle(self, cr, coord_pair, color, fillcolor, alpha, radius = None):

		if radius is None:
			radius = self.stroke_width

		from math import pi
		pos_x, pos_y = coord_pair

		cr.arc( pos_x, pos_y, radius, 0, 2*pi)
		self.color_with_alpha(cr, fillcolor, alpha)

		cr.fill_preserve()
		self.color_with_alpha(cr, color, alpha)
		cr.stroke()

	# -------------

	def button_press_event(self, widget, event):

		print "Highlighted node id:", self.gui_active_node_id

		# LEFT MOUSE BUTTON
		if event.button == 1:


			# Check for modifier keys...
			from gtk.gdk import CONTROL_MASK
			if event.state & CONTROL_MASK:
				print "Drag selection starting..."









			atom_ref = self.collection_reference.atom_on_deck
			if atom_ref != None:
				
				if self.gui_active_node_id != None:
					

					self.collection_reference.instantiated_nodes.append( atom_ref )
					self.collection_reference.B.add_node( atom_ref.id )					
					
					edge = (atom_ref.id, self.gui_active_node_id)
					self.gui_link.node_pool.post_removal_node_regeneration(edge, True)

					self.collection_reference.atom_on_deck = None	# atom_ref
					self.gui_link.node_adding_button.set_active(False)


					self.node_positions_by_label[atom_ref.id] = self.transform_point_inverse( (event.x, event.y) )
					self.node_reference_by_label[atom_ref.id] = atom_ref
					self.node_colors_by_label[atom_ref.id] = self.collection_reference.named_color[ atom_ref.atom_type ]


			elif self.gui_link.node_removing_button.get_active():
				if self.gui_active_node_id != None:
					self.collection_reference.remove_node( self.gui_active_node_id )

			else:
				if self.edge_adding_start_node != None:
					if self.gui_active_node_id != None:
						edge = (self.edge_adding_start_node, self.gui_active_node_id)
						self.gui_link.node_pool.post_removal_node_regeneration(edge, True)
						self.edge_adding_start_node = None
				else:
					if self.gui_link.selection_mode.get_active():	# Edge selection
						if self.active_edge != None:
							print '-'*20, "chop", '-'*20
							self.gui_link.node_pool.post_removal_node_regeneration( self.active_edge, False)

					else:						# Node selection
						if self.gui_active_node_id != None:
							print self.node_reference_by_label[ self.gui_active_node_id ]
		# RIGHT MOUSE BUTTON
		elif event.button == 3:

			if self.gui_link.node_adding_button.get_active() or self.gui_link.node_removing_button.get_active():
				self.gui_link.node_adding_button.set_active(False)
				self.gui_link.node_removing_button.set_active(False)
			else:
				if self.edge_adding_start_node == None:
					if self.gui_active_node_id != None:
						self.edge_adding_start_node = self.gui_active_node_id

						# Embedding this stuff way in here may be inappropriate later
						x = event.x
						y = event.y
						state = event.state	# Unnecessary, for now

						self.last_mouse_coords = (x, y)
				else:
					self.edge_adding_start_node = None




		if self.gui_link.auto_update_checkbox.get_active():
			self.gui_link.cb_rearrange(self)


		widget.queue_draw()

		return True

	# -------------

	def leave_notify_event(self, widget, event):

		print "Am I leaving?"
		self.gui_active_node_id = None
		self.active_edge = None



		treestore = self.gui_link.atom_props_treeview.get_model()
		my_iter = treestore.get_iter_first()

		treestore.set_value(my_iter, 1, -1)
		my_iter = treestore.iter_next(my_iter)

	# -------------

	def transform_point(self, point):
		'''Transforms the point coordinates using the same matrix as the drawing transform'''

		width, height = self.window.get_size()

		transformed_point = self.vector_add( point, self.vector_scale(self.upper_left, -1) )
		transformed_point = self.vector_scale( transformed_point, self.draw_scale )
		transformed_point = self.vector_add( transformed_point, ((width - self.draw_scale*self.original_width)/2.0, (height - self.draw_scale*self.original_height)/2.0) )
		return transformed_point

	# -------------

	def transform_point_inverse(self, point):
		'''Transforms the point coordinates using the inverse matrix as the drawing transform'''

		width, height = self.window.get_size()

		transformed_point = self.vector_add( point, (-(width - self.draw_scale*self.original_width)/2.0, -(height - self.draw_scale*self.original_height)/2.0) )
		transformed_point = self.vector_scale( transformed_point, 1.0/self.draw_scale )
		transformed_point = self.vector_add( transformed_point, self.upper_left )

		return transformed_point

	# -------------

	def motion_notify_event(self, widget, event):
		if event.is_hint:
			x, y, state = event.window.get_pointer()
		else:
			x = event.x
			y = event.y
			state = event.state	# Unnecessary, for now

		self.last_mouse_coords = (x, y)

		graph_reference = self.collection_reference.B


		min_dist = float('infinity')
		if self.gui_link.selection_mode.get_active():

			min_edge = None

			# Base proximity on distance from edge midpoints
			for edge in graph_reference.edges():

				from_node, to_node = edge
				from_point, to_point = self.node_positions_by_label[ int( from_node ) ], self.node_positions_by_label[ int( to_node ) ]

				midpoint = self.midpoint( from_point, to_point )
				dist = self.distance( (x, y), self.transform_point( midpoint ) )

				if dist < min_dist:
					min_dist = dist
					min_edge = edge

			self.active_edge = min_edge

		else:

			min_point = None

			for node_label in graph_reference.nodes():
				node = int( node_label )
				point = self.node_positions_by_label[ node ]

				dist = self.distance( (x, y), self.transform_point( point ) )

				if self.gui_link.hover_proximity.get_active():
					if dist < self.atom_radius * self.draw_scale:
						min_point = node
				else:
					if dist < min_dist:
						min_dist = dist
						min_point = node

				self.gui_active_node_id = min_point




				if self.gui_active_node_id != None:
					self.gui_link.refresh_active_node_info( self.gui_active_node_id )

				else:

					treestore = self.gui_link.atom_props_treeview.get_model()
					my_iter = treestore.get_iter_first()
					treestore.set_value(my_iter, 1, -1)


		print "FOO:", self.gui_active_node_id


		widget.queue_draw()

		return True

	# -------------

	def draw_line_from_selected_node(self, cr):

		mouse_target_point = self.last_mouse_coords

		node_draw_point = self.node_positions_by_label[ int( self.edge_adding_start_node ) ]
		screen_node_point = self.transform_point( node_draw_point )


 		cr.save()
		cr.identity_matrix()
		

		cr.set_line_width(self.stroke_width)
		self.color_with_alpha(cr, "green", 1.0)

		cr.move_to( *screen_node_point )
		cr.line_to( *mouse_target_point )
		cr.stroke()

 		cr.restore()

	# -------------

	def draw_graph_edges(self, cr):

		root_path_edges = []

		for network_segment in self.collection_reference.network_segment_locks:

			if self.active_edge:
				active_from, active_to = self.active_edge
			else:
				active_from, active_to = -1, -1

			cr.move_to( *self.node_positions_by_label[ network_segment.from_node_id ] )
			cr.line_to( *self.node_positions_by_label[ network_segment.to_node_id ] )


			if len(root_path_edges):
				if (network_segment.from_node_id, network_segment.to_node_id) in root_path_edges \
				or (network_segment.to_node_id, network_segment.from_node_id) in root_path_edges:
					self.color_with_alpha(cr, "green", 0.75)
					cr.set_line_width(2*self.stroke_width)
					cr.stroke_preserve()


			if (int(active_from), int(active_to)) == (network_segment.from_node_id, network_segment.to_node_id)\
			or (int(active_to), int(active_from)) == (network_segment.from_node_id, network_segment.to_node_id):
				self.color_with_alpha(cr, "red", 1.0)
			else:
				self.color_with_alpha(cr, "black", 1.0)



			cr.set_line_width(self.stroke_width)
			cr.stroke()

	# -------------

	def draw_graph_nodes(self, cr):



		for node in self.collection_reference.instantiated_nodes:

			cr.set_line_width(self.stroke_width)
			numeric_id = node.id
			cr.save()

			point = self.node_positions_by_label[ numeric_id ]

			cr.translate( *point )

			if numeric_id is self.gui_active_node_id:
				halo_color = (0.6, 0, 0.6, 0.5)	# purple halo
				if self.gui_link.node_removing_button.get_active():
					halo_color = (0.8, 0, 0, 0.8)	# red halo
				self.draw_halo(cr, (0, 0), self.halo_radius, halo_color)

			atom_ref = self.node_reference_by_label[ numeric_id ]

			from math import pi
			c = gtk.gdk.color_parse( self.node_colors_by_label[ numeric_id ] )
			cr.arc(0, 0, self.atom_radius, 0, 2*pi)

			bright_red = (1 - c.red)*0.7 + c.red
			bright_green = (1 - c.green)*0.7 + c.green
			bright_blue = (1 - c.blue)*0.7 + c.blue
			cr.set_source_rgb(bright_red, bright_green, bright_blue)
			cr.fill()

			cr.arc(0, 0, self.atom_radius, 0, 2*pi)
			cr.set_dash([self.dash_length])
			self.color_with_alpha(cr, "black", 1.0)
			cr.stroke()
			cr.set_dash([])

			if atom_ref.known_root_id == self.collection_reference.get_global_root_id():

				# Draw a white box
				cr.set_line_join(cairo.LINE_JOIN_ROUND)
				self.color_with_alpha(cr, "white", 1.0)
				cr.set_line_width(self.stroke_width)

				from math import sqrt
				inscribed_position = self.atom_radius/sqrt(2)
				cr.rectangle(-inscribed_position, -inscribed_position, 2*inscribed_position, 2*inscribed_position)
				cr.stroke()

			cr.restore()

	# -------------

	def draw_radioactive_symbol(self, cr, point):

		from math import pi

		cr.save()
		cr.translate( *point )

		self.color_with_alpha(cr, "blue", 0.5)
		for i in range(3):
			cr.move_to(0, 0)
			cr.rel_line_to(self.halo_radius, 0)
			cr.arc(0, 0, self.halo_radius, 0, pi/3 )
			cr.close_path()
			cr.fill()

			cr.rotate(2*pi/3)

		cr.restore()

	# -------------

	def draw_color_key(self, cr):
		cr.save()
		cr.identity_matrix()

		cr.translate(self.stroke_width/2.0, self.stroke_width/2.0)

		for i, color in enumerate( self.message_colors ):

			cr.rectangle(0, 0, 12, 8)
			self.color_with_alpha(cr, color, 0.5)
			cr.fill_preserve()
			self.color_with_alpha(cr, "black", 1.0)
			cr.stroke()

			cr.translate(12 + 2*self.stroke_width, 0)

		cr.restore()

	# -------------

	def draw_node_labels(self, cr):
		cr.select_font_face("FreeSerif")
		cr.set_font_size(self.atom_radius)

		for node in self.collection_reference.instantiated_nodes:
			numeric_id = node.id

			xbearing, ybearing, text_width, text_height, xadvance, yadvance = ( cr.text_extents( str(numeric_id) ) )
			x, y = self.node_positions_by_label[ numeric_id ]

			cr.move_to(x - xbearing - text_width / 2.0, y - ybearing - text_height / 2.0)
			self.color_with_alpha(cr, "black", 1.0)
			cr.show_text( str(numeric_id) )

	# -------------

	def draw(self, cr, width, height):
		'''This function determines the z-ordering of the graphical elements.'''

		potential_w_scale = width / (self.max_atom_padding + self.original_width)
		potential_h_scale = height / (self.max_atom_padding + self.original_height)
		self.draw_scale = min(potential_w_scale, potential_h_scale)

		# Center the drawing in the window
		cr.translate((width - self.draw_scale*self.original_width)/2.0, (height - self.draw_scale*self.original_height)/2.0)

		# Apply the scale transformation
		cr.scale(self.draw_scale, self.draw_scale)

		# Put the upper-left point at 0,0 in the drawing
		cr.translate( *self.vector_scale(self.upper_left, -1) )



		cr.set_line_join(cairo.LINE_JOIN_ROUND)
		graph_reference = self.collection_reference.B

		# Draw the edges
		self.draw_graph_edges(cr)

		# Mark leaf nodes
		self.mark_leaf_nodes(cr, graph_reference)

		# Draw the ports
		if self.gui_link.nubs_enabled_checkbox.get_active():
			self.draw_port_nubs(cr, graph_reference)


		# Draw the atoms
		self.draw_graph_nodes(cr)

		# Draw the labels
		self.draw_node_labels(cr)

		# Draw the color key
		self.draw_color_key(cr)
		
		# Draw the edge-adding line if needed
		if self.edge_adding_start_node != None:
			self.draw_line_from_selected_node(cr)

		if self.gui_link.node_adding_button.get_active():
		
			self.draw_floating_atom(cr)

