#! /usr/bin/env python
import pygtk
pygtk.require('2.0')
import gtk, cairo

from interactive_graph.cairo_graph import CairoGraph

from datetime import datetime

# ==========================================================

class RichGraph(CairoGraph):

	message_colors = ["green", "red", "blue", "yellow", "black"]

	# -------------

	port_colors = [(0, 0.7, 0, 1.0), (0.7, 0, 0, 1.0), (0, 0, 0.7, 1.0), (0.7, 0, 0.7, 1.0)]

	def draw_port_nubs(self, cr, graph_reference):
		cr.set_line_width(self.stroke_width/2.0)
		for edge in graph_reference.edges():

			from_node, to_node = edge
			from_point = self.node_positions_by_label[ int( from_node ) ]
			to_point = self.node_positions_by_label[ int( to_node ) ]

			from math import atan2, pi
			x_disp, y_disp = self.displacement( from_point, to_point )
			rotation_angle = atan2( y_disp, x_disp )	# In radians


			# ~~~~~~~~~~~~~~
			port_from = self.node_reference_by_label[ int(from_node) ].get_port_by_target( int(to_node) )

			cr.save()
			cr.translate( *from_point )
			cr.rotate( rotation_angle )
			cr.translate( self.atom_radius, 0 )


			if self.gui_link.animation_enabled:
				if len(port_from.outgoing_message_queue.activeQ):
				
					cr.arc( 0, 0, self.atom_radius/1.5, 0, 2*pi)
				
					self.color_with_alpha(cr, "black", 0.5)
					cr.set_line_width(2*self.stroke_width)
					cr.stroke()


				if type(port_from.pending_aggregation_message) is list:
				
					cr.arc( 0, 0, self.atom_radius/1.0, 0, 2*pi)
				
					self.color_with_alpha(cr, "yellow", 0.7)
					cr.set_line_width(2*self.stroke_width)
					cr.stroke()

			cr.set_line_width(self.stroke_width)
			cr.arc( 0, 0, self.atom_radius/2.5, 0, 2*pi)

			port_port_status = port_from.port_status
			cr.set_source_rgba( *self.port_colors[ port_port_status ] )

			cr.fill_preserve()
			self.color_with_alpha(cr, "black", 1.0)
			cr.stroke()
			cr.restore()


			# ~~~~~~~~~~~~~~
			port_to = self.node_reference_by_label[ int(to_node) ].get_port_by_target( int(from_node) )

			cr.save()
			cr.translate( *to_point )
			cr.rotate( rotation_angle )
			cr.translate( -self.atom_radius, 0 )



			if self.gui_link.animation_enabled:
				if len(port_to.outgoing_message_queue.activeQ):
				
					cr.arc( 0, 0, self.atom_radius/1.5, 0, 2*pi)
				
					self.color_with_alpha(cr, "black", 0.5)
					cr.set_line_width(2*self.stroke_width)
					cr.stroke()

				if type(port_to.pending_aggregation_message) is list:
				
					cr.arc( 0, 0, self.atom_radius/1.0, 0, 2*pi)
				
					self.color_with_alpha(cr, "yellow", 0.7)
					cr.set_line_width(2*self.stroke_width)
					cr.stroke()


			cr.set_line_width(self.stroke_width)
			cr.arc( 0, 0, self.atom_radius/2.5, 0, 2*pi)

			port_port_status = port_to.port_status
			cr.set_source_rgba( *self.port_colors[ port_port_status ] )

			cr.fill_preserve()
			self.color_with_alpha(cr, "black", 1.0)
			cr.stroke()
			cr.restore()

	# -------------
	# Mark leaf nodes
	def mark_leaf_nodes(self, cr, graph_reference):

		from brains import LinePort

		for node in self.collection_reference.instantiated_nodes:

			if node.is_leaf():
				point = self.node_positions_by_label[ node.id ]

				# Draw "radioactive symbol" if the node is a leaf node
				self.draw_radioactive_symbol(cr, point)

	# -------------

	def draw_floating_atom(self, cr):

 		cr.save()
		cr.identity_matrix()

		if self.gui_active_node_id != None:
			mouse_target_point = self.last_mouse_coords
			node_draw_point = self.node_positions_by_label[ int( self.gui_active_node_id ) ]
			screen_node_point = self.transform_point( node_draw_point )

			cr.set_line_width(self.stroke_width)
			self.color_with_alpha(cr, "blue", 1.0)
			cr.move_to( *screen_node_point )
			cr.line_to( *mouse_target_point )
			cr.stroke()

		# Atom circle
		atom_ref = self.gui_link.atom_collection.atom_on_deck
		if atom_ref == None:
			print "There is no atom on deck.  What the heck?"
			return

		cr.set_dash([self.dash_length], 2*self.dash_length*datetime.now().microsecond/1000000.0)
		self.draw_simple_circle(	cr,
						self.last_mouse_coords,
						"black",
						self.gui_link.atom_collection.named_color[ atom_ref.atom_type ],
						1.0,
						self.atom_radius)
		cr.set_dash([])


		# Atom label
		node_label = str( atom_ref.id )
		cr.select_font_face("FreeSerif")
		cr.set_font_size(self.atom_radius)
		xbearing, ybearing, text_width, text_height, xadvance, yadvance = ( cr.text_extents( node_label ) )

		x, y = self.last_mouse_coords

		cr.move_to(x - xbearing - text_width / 2, y - ybearing - text_height / 2)
		self.color_with_alpha(cr, "black", 1.0)
		cr.show_text( node_label )


 		cr.restore()

