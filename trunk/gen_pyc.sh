#!/usr/bin/env python

import sys, os

pathname = os.path.dirname(sys.argv[0])
fullpath =  os.path.abspath(pathname)
os.chdir(fullpath)
sys.path.append("./app")
sys.path.append("./app/visual")
sys.path.append("./app/visual/interactive_graph")


import brains, node_pool, animation, rich_graph, cairo_drawlib, cairo_graph, user_interface, vector_math
