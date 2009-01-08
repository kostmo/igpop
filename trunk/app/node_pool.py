from pygraphviz import AGraph
from random import choice, sample
import shelve, threading
from datetime import datetime

from visual.interactive_graph.animation import AnimationEvent

from brains import BasicNode, LinePort

# ===============================================

class NetworkSegment:
	def __init__ (self, from_node_id, to_node_id):

		self.from_node_id = from_node_id
		self.to_node_id = to_node_id

	# ----------------------------------

	def get_connected_node_id(self, from_node):
		if from_node == self.to_node_id:
			return self.from_node_id
		else:
			return self.to_node_id

# ===============================================

class NodePool:

	MAX_ATOM_ID = 50

	atom_types = [
		"Alpha",
		"Beta",
		"Delta"
	]

	standard_color = [
		"#FF3030",	#red
		"#30FF30",	#green
		"#3030FF"	#blue
	]

	named_color = [
		"red",
		"blue",
		"green"
	]

	# ---------------------------------------

	def __init__ (self, gui_link):

		self.sim_running = False
		self.start_wallclock_time = None

		self.gui_link = gui_link
		self.number_of_atoms = 12
		self.atom_on_deck = None	# For edge addition purposes

	# ---------------------------------------

	def cb_save_graph(self, filename):

		myfile = shelve.open(filename)

		edge_list = []
		for edge in self.B.edges():
			v1, v2 = edge
			tuple_edge = (int(v1), int(v2))
			edge_list.append( tuple_edge )

		myfile["graph"] = edge_list

		myfile.close()

	# ---------------------------------------

	def cb_load_graph(self, filename):

		myfile = shelve.open(filename)
		if not myfile:
			print filename, "could not be found"
			return

		self.B = AGraph()
		for edge in myfile["graph"]:
			self.B.add_edge( *edge )

		myfile.close()

		self.B.layout()
		self.instantiate_atoms()

		self.gui_link.cairograph.regen_points( self )
		self.gui_link.cairograph.queue_draw()

	# ---------------------------------------

	def generate_new_graph(self):

		import networkx
		if not self.gui_link.use_preset.get_active():
			# Create a random graph
			G = networkx.fast_gnp_random_graph(self.number_of_atoms, 0.20)

			# Prune the "forest" down to the largest single connected component
			connecteds = networkx.connected_components( G )
			if len(connecteds) > 1:
				for nodelist in connecteds[1:]:
					for node in nodelist:
						G.delete_node( node )

			A = networkx.to_agraph(G)



			# Now replace node IDs with random numbers in the range [0, 99]
			replacement_nodes = sample( range(self.MAX_ATOM_ID), A.order() )
			lookup_table = {}
			for node in A.nodes():
				lookup_table[ int(node) ] = replacement_nodes.pop()
			self.B = AGraph()
			for edge in A.edges():
				u, v = edge
				self.B.add_edge( lookup_table[int(u)], lookup_table[int(v)] )


		else:
			self.B = AGraph()

			self.B.add_edge(2, 7)
			self.B.add_edge(7, 3)
			self.B.add_edge(7, 4)
#			self.B.add_edge(4, 3)

			self.B.add_edge(4, 6)
			self.B.add_edge(3, 6)

		self.instantiate_atoms()

	# ---------------------------------------

	def cb_add_node(self, widget):

		if widget.get_active():

			self.gui_link.selection_mode.get_group()[1].set_active(True)
			self.gui_link.node_removing_button.set_active(False)

			taken_integers = []
			for node in self.B.nodes():
				taken_integers.append( int(node) )

			available_integers = set( range(self.MAX_ATOM_ID) ).difference( set(taken_integers) )
			node_id = choice( list(available_integers) )
			atom_type = choice( range(len(self.atom_types)) )


			self.atom_on_deck = BasicNode(self, node_id, atom_type)
			print "Created an atom for the deck..."
		else:
			self.atom_on_deck = None

	# ---------------------------------------

	def remove_node(self, node_id):

		atom_ref = self.get_atom_by_label( node_id )

		for port_out_from in atom_ref.ports:

			connected_node_reference = port_out_from.connected_node
			for port_into in connected_node_reference.ports:
				if port_into.connected_node.id == node_id:

					port_into.parent_node.ports.remove( port_into )

			self.network_segment_locks.remove( port_out_from.network_segment )


		self.instantiated_nodes.remove( atom_ref )
		self.B.delete_node(node_id)

	# ---------------------------------------

	def get_atom_by_label(self, numeric_label):
		for myatom in self.instantiated_nodes:
			if numeric_label is myatom.id:
				return myatom

	# ---------------------------------------

	def get_network_segment(self, local_id, remote_id):
		for segment in self.network_segment_locks:
			if segment.from_node_id == local_id and segment.to_node_id == remote_id\
			    or segment.to_node_id == local_id and segment.from_node_id == remote_id:
				return segment

	# ---------------------------------------

	def instantiate_atoms(self):

		self.instantiated_nodes = []
		for node in self.B.nodes():
			atom_type = choice( range(len(self.atom_types)) )
			self.instantiated_nodes.append( BasicNode(self, node, atom_type) )

		self.instantiate_segments()

	# ---------------------------------------

	def instantiate_segments(self):

		self.network_segment_locks = []
		for from_node_string, to_node_string in self.B.edges():
			segment = NetworkSegment(int(from_node_string), int(to_node_string))
			self.network_segment_locks.append( segment )

		self.renew_ports()

	# ---------------------------------------

	def renew_ports(self):

		# Record references to the neighboring atoms' threads
		for atomthread in self.instantiated_nodes:
			atomthread.establish_neighbors()

	# ---------------------------------------

	def post_removal_node_regeneration(self, active_edge, adding):

		u, v = active_edge
		from_node_number = int(u)
		to_node_number = int(v)

		from_node_reference = self.get_atom_by_label( from_node_number )
		to_node_reference = self.get_atom_by_label( to_node_number )

		if adding:
			self.B.add_edge( from_node_number, to_node_number )

			segment = NetworkSegment(from_node_number, to_node_number)
			self.network_segment_locks.append( segment )

			from_node_reference.ports.append( LinePort(from_node_reference, to_node_reference) )
			to_node_reference.ports.append( LinePort(to_node_reference, from_node_reference) )

		else:
			self.B.delete_edge( from_node_number, to_node_number )

			# Regenerate neighbor list/ports
			for port in from_node_reference.ports:
				if port.connected_node.id == to_node_number:
					from_node_reference.ports.remove( port )

			for port in to_node_reference.ports:
				if port.connected_node.id == from_node_number:
					to_node_reference.ports.remove( port )
					self.network_segment_locks.remove( port.network_segment )

		self.gui_link.repopulate_atom_list()

	# ---------------------------------------

	def get_global_root_id(self):

		min_node_id = float('infinity')
		
		for atom in self.instantiated_nodes:
			if atom.id < min_node_id:
				min_node_id = atom.id

		return min_node_id

