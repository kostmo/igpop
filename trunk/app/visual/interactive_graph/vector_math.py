#! /usr/bin/env python

# =============

class VectorMath:

	def vector_scale(self, vector, scalar):
		x, y = vector
		return (x*scalar, y*scalar)

	# -------------

	def midpoint(self, first_point, second_point):
		return self.vector_scale(self.vector_add(first_point, second_point), 0.5)

	# -------------

	def vector_add(self, first_point, second_point):
		x1, y1 = first_point
		x2, y2 = second_point
		return (x1 + x2, y1 + y2)

	# -------------

	def displacement(self, start_point, end_point):
		x1, y1 = start_point
		x2, y2 = end_point
		return (x2 - x1, y2 - y1)

	# -------------

	def distance(self, start_point, end_point):
		return self.magnitude(self.displacement(start_point, end_point))

	# -------------

	def magnitude(self, vector_2d):
		from math import sqrt
		x, y = vector_2d
		return sqrt(x*x + y*y)

	# -------------

	def interpolate(self, start_point, end_point, fraction):
		resultant = self.vector_add(start_point, self.vector_scale(self.displacement(start_point, end_point), fraction) )
		return resultant

