from random import random
from datetime import datetime, timedelta

from visual.interactive_graph.animation import AnimationEvent

# ===============================================

# Link states:

class LinePort:

	DESIGNATED_PORT = 0
	ROOT_PORT = 1
	BLOCKING_PORT = 2
	REJECTED_PORT = 3
	status_labels = ["DESIGNATED_PORT", "ROOT_PORT", "BLOCKING_PORT", "REJECTED_PORT"]


	def __init__ (self, parent_node, bridge_connected_to_this_port):

		self.queued_message_types = []

		self.last_hello_msg = None

		self.port_status = self.DESIGNATED_PORT

		# Housekeeping stuff:
		self.parent_node = parent_node
		self.connected_node = bridge_connected_to_this_port

		self.blockage_animation = None

		self.network_segment = self.parent_node.collection.get_network_segment(self.parent_node.id, self.connected_node.id)

		self.pending_aggregation_message = None
	# ---------------------------------------

	def __str__(self):
		output = "Port to " + str(self.connected_node.id) + ", Status: " + str(self.status_labels[self.port_status]) + ", Last HELLO msg:"
		output += "\n\t"
		output += str(self.last_hello_msg)
		return output

	# ----------------------------------

	def signify_blockage(self):

		animation_duration = self.parent_node.collection.gui_link.blockage_duration_control.get_value()
		self.blockage_animation = AnimationEvent(animation_duration)

		self.blockage_port_id = self.parent_node.id

# ===============================================

class BasicNode():

	def __init__(self, collection, graph_node, atom_type):

		self.collection = collection	# More housekeeping stuff...
		self.main_graph = self.collection.B


		self.id = int(graph_node)
		self.atom_type = atom_type
		self.known_root_id = self.id
		self.ports = []

	# ============================

	def __str__(self):

		printable_string = '-'*30
		printable_string += "\n"
		printable_string += str(self.id) + " - " + self.collection.atom_types[self.atom_type]
		printable_string += "\nAssumed root ID: " + str(self.known_root_id)
		printable_string += "\nPath length to assumed root: " + str(self.get_root_path_length())
		printable_string += "\nLink states:"
		for port in self.ports:
			printable_string += "\n"
			printable_string += str(port)

		return printable_string

	# ============================

	def establish_neighbors(self):

		neighbor_list = []

		current_atom_neighbors = self.main_graph.neighbors( self.id )
		for neighbor_index in current_atom_neighbors:
			for atomthread in self.collection.instantiated_nodes:
				if atomthread.id == int(neighbor_index):
					neighbor_list.append( atomthread )
					break

		self.initialize_ports( neighbor_list )

	# ============================

	def initialize_ports(self, neighbor_list):

		self.neighbor_threads = neighbor_list

		self.ports = []
		for neighbor in self.neighbor_threads:
			self.ports.append( LinePort(self, neighbor) )

	# ============================

	def determine_port_statuses(self):

		min_root_port = None
		min_root_port_id = float('infinity')

		for port in self.ports:

			port.previous_port_status = port.port_status


			reported_path_length = port.last_hello_msg.root_path_length

			if port.port_status != LinePort.REJECTED_PORT:
				port.port_status = LinePort.DESIGNATED_PORT	# Default assignment

			if port.last_hello_msg.assumed_root_id <= self.known_root_id:

				if port.last_hello_msg.root_path_length < self.get_root_path_length():

					port.port_status = LinePort.BLOCKING_PORT

					if port.connected_node.id < min_root_port_id:
						min_root_port_id = port.connected_node.id
						min_root_port = port

				elif port.last_hello_msg.root_path_length == self.get_root_path_length():
						port.port_status = LinePort.BLOCKING_PORT

		if min_root_port != None:
			min_root_port.port_status = LinePort.ROOT_PORT




		# Respond to a change to root port status:
		for port in self.ports:
			if port.previous_port_status == LinePort.DESIGNATED_PORT and port.port_status != LinePort.DESIGNATED_PORT:

				# Renege all queued hello messages on this port
				port.port_specific_renege_event.signal()
				print "Port from", port.parent_node.id, "to", port.connected_node.id, "is no longer a DESIGNATED PORT"



		# Seems like a good place to do a GUI update:
		self.collection.gui_link.refresh_global_info_labels()

	# ============================
	# HELPER FUNCTIONS START HERE:
	# ============================

	def get_root_path_length(self):

		if self.known_root_id == self.id:
			return 0

		min_root_path_length = float('infinity')

		for port in self.ports:
			if port.last_hello_msg.assumed_root_id <= self.known_root_id:
				if port.last_hello_msg.root_path_length < min_root_path_length:
					min_root_path_length = port.last_hello_msg.root_path_length

		return min_root_path_length + 1

	# ============================

	def is_leaf(self):
		for port in self.ports:
			if port.port_status == LinePort.DESIGNATED_PORT:
				return False
		return True

	# ============================

	def get_upstream_port(self):
		for port in self.ports:
			if port.port_status == LinePort.ROOT_PORT:
				return port

	# ============================

	def get_port_by_target(self, numeric_label):
		for port in self.ports:
			if port.connected_node.id is numeric_label:
				return port

	# ============================

	def get_connected_port(self, port_towards_neighbor):
		receiving_port_of_neighbor = None

		for port in port_towards_neighbor.connected_node.ports:

			if port.connected_node.id is self.id:
				receiving_port_of_neighbor = port
				break

		return receiving_port_of_neighbor

