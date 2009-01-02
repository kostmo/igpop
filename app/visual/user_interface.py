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

		self.cairograph.regen_points( self.node_pool )
		self.cairograph.queue_draw()

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

			# Help menu:
			"cb_about":			self.cb_about,

			# Buttons:
			"cb_rearrange":		self.cb_rearrange,
			"cb_screenshot":	self.cb_screenshot,
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
		workspace_hbox = xml_tree.get_widget( "workspace_hbox" )
		workspace_hbox.pack_start(self.cairograph, True, True)

		self.cb_regenerate_tree(None)







		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		# FIXME
		self.node_adding_button = gtk.ToggleButton("Add Node")
		self.node_adding_button.connect("toggled", self.node_pool.cb_add_node)
#		button_vbox.pack_start(self.node_adding_button, False, False)

		self.node_removing_button = gtk.ToggleButton("Remove Node")
		self.node_removing_button.connect("toggled", self.cb_remove_node)
#		button_vbox.pack_start(self.node_removing_button, False, False)
		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




		self.selection_mode = xml_tree.get_widget( "radiobutton2" )
		self.hover_proximity = xml_tree.get_widget( "radiobutton4" )


		# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
		self.show_all()


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

	def cb_rearrange(self, widget):
		self.node_pool.B.layout()
		self.cairograph.regen_points( self.node_pool )
		self.cairograph.queue_draw()

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

		f.set_current_name("untitled.graph")

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

	gobject.threads_init()
	display = NetworkGraphDisplay()
	gtk.main()

# ===============================

if __name__ == "__main__":

	main()

