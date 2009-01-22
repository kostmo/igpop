#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk, gobject, pango
import gtk.glade

from time import sleep
from datetime import datetime
import threading

from rich_graph import RichGraph
from node_pool import NodePool

# =============

class NetworkGraphDisplay(gtk.Window):

	app_title = "IGPop Graph Editor"

	# when invoked (via signal delete_event), terminates the application.
	def close_application(self, widget, event, data=None):
		self.end_program(widget)
		return False

	# ---------------------------------------

	def cb_regenerate_tree(self, widget):
		self.node_pool = NodePool(self)
		self.node_pool.generate_new_graph()


		self.cb_rearrange(widget)

		self.repopulate_atom_list()

	# --------------------------------
	def cb_about(self, widget):

		a = gtk.AboutDialog()

		img = gtk.Image()
		img.set_from_file("visual/icon.svg")
		a.set_logo(img.get_pixbuf())

		a.set_authors(["Karl Ostmo"])
		a.set_name( self.get_title() )
		a.set_website("http://igpop.googlecode.com/")
		a.set_transient_for( self )
		a.run()
		a.destroy()

	# ---------------------------------------

	def __init__(self):


		gtk.Window.__init__(self)



		self.connect("key-release-event", self.cb_key_release)
		self.connect("key-press-event", self.cb_key_press)
		self.connect("focus-out-event", self.cb_focus_out)	# EXPERIMENTAL


		self.multi_select_modifier_down = False


		self.animation_enabled = False


		self.connect("delete_event", self.close_application)
		self.set_title( self.app_title )
		self.set_icon_from_file("visual/icon.svg")


		gladefile = "interface.glade"
		guts_widget_name = "main_vbox"
		xml_tree = gtk.glade.XML(gladefile, guts_widget_name, domain="surrogate_window")



		callbacks = {
			# File menu:
			"cb_regenerate":	self.cb_regenerate_tree,
			"cb_load":			self.cb_load_file_name,
			"cb_save":			self.cb_set_file_name,
			"cb_quit":			self.end_program,

			# View menu:
			"cb_conditional_graph_update":	self.cb_conditional_graph_update,
			"cb_update_graph":	self.cb_update_graph,

			# Help menu:
			"cb_about":			self.cb_about,

			# Buttons:
			"cb_rearrange":		self.cb_rearrange,
			"cb_screenshot":	self.cb_screenshot,
			"cb_remove_node":	self.cb_remove_node,
			"cb_add_node":		self.cb_add_node,

			# Toolbar:
#			"cb_fullscreen":	self.cb_fullscreen,

		}

		# Assign menu callbacks:
		xml_tree.signal_autoconnect(callbacks)



		main_vbox = xml_tree.get_widget( guts_widget_name )
		self.add(main_vbox)


		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		liststore = gtk.ListStore(str, int)
		for i, dimension in enumerate(["Node ID"]):
			liststore.append([dimension, i])


		self.atom_props_treeview = xml_tree.get_widget( "treeview1" )
		self.atom_props_treeview.set_model(liststore)


		for i, new_col_label in enumerate(["Property", "Value"]):
			cell = gtk.CellRendererText()
			tvcolumn = gtk.TreeViewColumn(new_col_label, cell, text=i)
			tvcolumn.set_expand(True)
			tvcolumn.set_clickable(True)
			if i>0:
				tvcolumn.set_cell_data_func(cell, self.treeview_unsigned_int_format)
			self.atom_props_treeview.append_column(tvcolumn)


		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		treestore = gtk.TreeStore(int)

		self.nodelist_treeview = xml_tree.get_widget( "treeview2" )
		self.nodelist_treeview.set_model(treestore)


		for i, new_col_label in enumerate(["Node ID"]):
			cell = gtk.CellRendererText()

			tvcolumn = gtk.TreeViewColumn(new_col_label, cell, text=i)
			tvcolumn.set_sort_column_id(i)	# This is abusing the purpose of the sort ID for later
			tvcolumn.set_expand(True)
			tvcolumn.set_clickable(True)
			if i>0:
				tvcolumn.set_cell_data_func(cell, self.treeview_float_format)
			self.nodelist_treeview.append_column(tvcolumn)

		self.use_preset = xml_tree.get_widget( "checkbutton1" )

		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

		self.cairograph = RichGraph(self)
		self.cairograph.set_size_request(300, 300)
		workspace_vbox = xml_tree.get_widget( "workspace_vbox" )
		workspace_vbox.pack_start(self.cairograph, True, True)



		self.selection_mode = xml_tree.get_widget( "radiobutton2" )
		self.hover_proximity = xml_tree.get_widget( "radiobutton4" )

		self.nubs_enabled_checkbox = xml_tree.get_widget( "nubs_enabled_checkbox" )
		self.auto_update_checkbox = xml_tree.get_widget( "auto_update_checkbox" )






		# Note: These are also in networkx.drawing.layout
		# see what happens when you call dir(networkx.drawing.layout)
		cb1 = xml_tree.get_widget( "combobox1" )
#		self.layout_possibilities = ["circular", "random", "shell", "spring", "spectral"]

		self.layout_possibilities = ["neato", "dot", "twopi", "circo", "fdp"]	# , "nop"

		for x in self.layout_possibilities:
			cb1.append_text( x )

		cb1.set_active(0)

		self.layout_selection = cb1


		cb2 = xml_tree.get_widget( "combobox2" )
		self.graph_possibilities = ["fast_gnp_random_graph", "gnp_random_graph", "dense_gnm_random_graph", "gnm_random_graph", "erdos_renyi_graph", "binomial_graph", "newman_watts_strogatz_graph", "watts_strogatz_graph", "random_regular_graph", "barabasi_albert_graph", "powerlaw_cluster_graph", "random_lobster", "random_shell_graph", "random_powerlaw_tree", "random_powerlaw_tree_sequence"]
		for x in self.graph_possibilities:
			cb2.append_text( x )

		cb2.set_active(0)

		self.random_graph_selection = cb2



		layout = cb2.get_children()[0]
		only_cell = layout.get_cells()[0]
#		only_cell.set_fixed_size(-1, -1)	# This does nothing.

#		only_cell.props.ellipsize = pango.ELLIPSIZE_END

		'''

		b1 = xml_tree.get_widget( "hbox1" )



		cell = gtk.CellRendererText()
		cell
		ls = gtk.ListStore( str )
		for x in layout_possibilities:
			ls.append( [x] )
		cb1 = gtk.ComboBox( ls )
		cb1.pack_start( cell, True )
		b1.pack_start(cb1, True, True)



		b2 = xml_tree.get_widget( "hbox5" )



		cell = gtk.CellRendererText()
		cell.props.ellipsize = pango.ELLIPSIZE_END
		ls = gtk.ListStore( object )
		for x in graph_possibilities:
			ls.append( [x] )
		cb2 = gtk.ComboBox( ls )
		cb2.pack_start( cell, True )
		b2.pack_start(cb2, True, True)
		'''







		self.cb_regenerate_tree(None)
		self.node_adding_button = xml_tree.get_widget("node_add_button")
		self.node_removing_button = xml_tree.get_widget("node_remove_button")





		self.fullscreen_toggle_action = gtk.ToggleAction("fullscreen_name", "Fullscreen", "Toggle fullscreen mode", gtk.STOCK_FULLSCREEN)

		self.fullscreen_toggle_action.connect_proxy( xml_tree.get_widget("fullscreen_menu_item") )
		self.fullscreen_toggle_action.connect_proxy( xml_tree.get_widget("fullscreen_toolbar_item") )

		self.fullscreen_toggle_action.connect("toggled", self.cb_fullscreen)




		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		self.show_all()


	# --------------------------------
	def cb_fullscreen(self, widget):

		if widget.get_active():

			# These are only required if we want to restrict window resizing
#			self.set_resizable( True )
#			while gtk.events_pending():
#				gtk.main_iteration(False)

			self.fullscreen()
		else:
			self.unfullscreen()
#			self.set_resizable( False )

	# ---------------------------------------

	def cb_conditional_graph_update(self, widget):

		if self.auto_update_checkbox.get_active():
			self.cb_rearrange(widget)

	# ---------------------------------------

	def cb_update_graph(self, widget):

		self.cairograph.queue_draw()

	# ---------------------------------------

	def refresh_active_node_info(self, node_id):

		node_ref = self.cairograph.node_reference_by_label[ node_id ]

		treestore = self.atom_props_treeview.get_model()

		my_iter = treestore.get_iter_first()
		treestore.set_value(my_iter, 1, node_id)

#		my_iter = treestore.iter_next(my_iter)
#		treestore.set_value(my_iter, 1, node_ref.get_root_path_length())

#		my_iter = treestore.iter_next(my_iter)
#		treestore.set_value(my_iter, 1, node_ref.known_root_id)

	# ---------------------------------------

	def repopulate_atom_list(self):
		treestore = self.nodelist_treeview.get_model()
		treestore.clear()


		for node in self.node_pool.instantiated_nodes:
			last_parent = treestore.append(None, [node.id])
			for port in node.ports:
				treestore.append(last_parent, [port.connected_node.id])

	# -------------------------------------------

	def treeview_unsigned_int_format(self, column, cell_renderer, tree_model, iter):
		pyobj = tree_model.get_value(iter, 1)
		if pyobj >= 0:
			cell_renderer.set_property('text', "%d" % pyobj)
		else:
			cell_renderer.set_property('text', "N/A")

	# -------------------------------------------

	def treeview_float_format(self, column, cell_renderer, tree_model, iter):
		pyobj = tree_model.get_value(iter, 1)
		cell_renderer.set_property('text', "%.2f" % pyobj)

	# -------------------------------------------

	def treeview_float_format_reverse(self, column, cell_renderer, tree_model, iter):
		pyobj = tree_model.get_value(iter, 0)
		cell_renderer.set_property('text', "%.2f" % pyobj)

	# ---------------------------------------
	
	def refresh_global_info_labels(self):




		treestore2 = self.global_info_treeview2.get_model()
		my_iter2 = treestore2.get_iter_first()



		# TODO: The atom count and channel count should only be updated whenever
		# a node or an edge is added or deleted.
		total_atom_count = len(self.node_pool.instantiated_nodes)
#		self.global_atomcount_label.set_text("%d" % total_atom_count)
		treestore2.set_value(my_iter2, 1, total_atom_count)




#		total_channel_count = len(self.node_pool.B.edges())
#		self.global_channelcount_label.set_text("%d" % total_channel_count)



		leaf_count = 0
		for node in self.node_pool.instantiated_nodes:
			if node.is_leaf():
				leaf_count += 1
#		self.global_leafcount_label.set_text("%d" % leaf_count)
		my_iter2 = treestore2.iter_next(my_iter2)
		my_iter2 = treestore2.iter_next(my_iter2)
		treestore2.set_value(my_iter2, 1, leaf_count)


	# ---------------------------------------

	def cb_focus_out(self, widget, event):
		# Since we can't observe whether the user releases the key when our window lacks focus,
		# we just force the key to be released, to avoid a "stuck-on" state.

		self.cairograph.window.set_cursor(None)

	# ---------------------------------------

	def cb_key_press(self, widget, event):
		print "Key pressed"
		self.multi_select_modifier_down = True

		from gtk.gdk import CONTROL_MASK, SHIFT_MASK
#		if event.state & (CONTROL_MASK | SHIFT_MASK):	# This does the same thing as the next line!
		if event.state & CONTROL_MASK:
			c = gtk.gdk.Cursor(gtk.gdk.CROSSHAIR)
			self.cairograph.window.set_cursor(c)

	# ---------------------------------------

	def cb_key_release(self, widget, event):
		print "Key released"
		self.multi_select_modifier_down = False


		from gtk.gdk import CONTROL_MASK
		if event.state & CONTROL_MASK:
			self.cairograph.window.set_cursor(None)

	# ---------------------------------------

	def cb_rearrange(self, widget):
		self.node_pool.B.layout( prog=self.layout_possibilities[ self.layout_selection.get_active() ] )
		self.cairograph.regen_points( self.node_pool )
		self.cairograph.queue_draw()

	# ---------------------------------------

	def cb_add_node(self, widget):

		self.node_pool.cb_add_node(widget)

	# ---------------------------------------

	def cb_remove_node(self, widget):
		if widget.get_active():

			self.selection_mode.get_group()[1].set_active(True)
			self.node_adding_button.set_active(False)

	# ---------------------------------------

	def cb_screenshot(self, widget):

		f = gtk.FileChooserDialog( action=gtk.FILE_CHOOSER_ACTION_SAVE )
		f.set_local_only(True)
		f.set_select_multiple(False)
		f.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)

		file_filter = gtk.FileFilter()
		file_filter.add_pattern("*")
		file_filter.set_name("All files")
		f.add_filter(file_filter)

		f.set_current_name("capture")

		response = f.run()
		filename = f.get_filename()

		f.destroy()


		if response == gtk.RESPONSE_OK:

			width, height = self.cairograph.window.get_size()
			self.cairograph.save_image_to_file(filename, width, height)

	# ---------------------------------------

	def cb_set_file_name(self, widget):

		f = gtk.FileChooserDialog( action=gtk.FILE_CHOOSER_ACTION_SAVE )
		f.set_local_only(True)
		f.set_select_multiple(False)
		f.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)

		file_filter = gtk.FileFilter()	# NEW
		file_filter.add_pattern("*.graph")
		file_filter.set_name("GraphViz file")
		f.add_filter(file_filter)

		file_filter = gtk.FileFilter()
		file_filter.add_pattern("*")
		file_filter.set_name("All files")
		f.add_filter(file_filter)

		f.set_current_name("untitled.graph")

		response = f.run()
		filename = f.get_filename()

		f.destroy()


		if response == gtk.RESPONSE_OK:
			self.node_pool.cb_save_graph(filename)

	# ---------------------------------------

	def cb_load_file_name(self, widget):

		f = gtk.FileChooserDialog()
		f.set_local_only(True)
		f.set_select_multiple(False)
		f.add_buttons(gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)

		file_filter = gtk.FileFilter()	# NEW
		file_filter.add_pattern("*.graph")
		file_filter.set_name("GraphViz file")
		f.add_filter(file_filter)

		file_filter = gtk.FileFilter()
		file_filter.add_pattern("*")
		file_filter.set_name("All files")
		f.add_filter(file_filter)

		response = f.run()
		filename = f.get_filename()

		f.destroy()

		if response == gtk.RESPONSE_OK:
			self.node_pool.cb_load_graph(filename)

	# ---------------------------------------

	def ticker(self):
		self.cairograph.queue_draw()
		sleep( 1/30.0 )	# Limit to 30 fps so as to not max out the processor
		return self.animation_enabled

	# ---------------------------------------

	def end_program(self, widget):

		gtk.main_quit()

	# ---------------------------------------




def main():

	display = NetworkGraphDisplay()
	gtk.main()

# ===============================


if __name__ == "__main__":

	main()
