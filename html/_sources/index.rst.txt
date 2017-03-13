.. Graph documentation master file, created by
   sphinx-quickstart on Fri Mar 10 16:27:04 2017.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Graph's documentation!
=================================

.. toctree::
   :maxdepth: 2
   :caption: Contents:  
   
   graphclass.rst
   algorithms.rst

.. rubric:: **Graph Class**

.. autosummary:: 
	graph.Graph

.. rubric:: **Methods**
	
.. rubric:: Construction Methods
.. autosummary:: 

	graph.Graph.add_edges
	graph.Graph.add_nodes
	graph.Graph.new_projection
	graph.Graph.new_subgraph
	
.. rubric:: Local Graph Methods
.. autosummary:: 

	graph.Graph.send_collect
	graph.Graph.update_edges
	graph.Graph.update_nodes
	
.. rubric:: Query Methods
	
.. autosummary:: 
	graph.Graph.nodes
	graph.Graph.find


.. rubric:: **Additional Classes and Algorithms**

.. autosummary:: 
	graph.algorithms.GraphLabel
	graph.algorithms.out_degree
	graph.algorithms.page_rank
	graph.algorithms.connected_comp

	

Indices and tables
==================
* :ref:`genindex`
* :ref:`search`
