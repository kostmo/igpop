#! /usr/bin/env python

from datetime import datetime, timedelta

# =============

class AnimationEvent:

	def __init__ (self, duration):
		self.begin_time = datetime.now()
		self.end_time = self.begin_time + timedelta(seconds = duration)

	# -------------

	def get_countdown_fraction(self):

		fraction_left = 0.0
		if datetime.now() < self.end_time:
			if datetime.now() >= self.begin_time:

				numerator_timediff = datetime.now() - self.begin_time
				numerator_ms = numerator_timediff.seconds*1000000.0 + numerator_timediff.microseconds

				denominator_timediff = self.end_time - self.begin_time
				denominator_ms = denominator_timediff.seconds*1000000.0 + denominator_timediff.microseconds

				fraction_left = numerator_ms / denominator_ms
			else:
				fraction_left = 1.0

		return fraction_left

