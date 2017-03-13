class GraphLabel():
    """A dict-like convenience wrapper object for graph nodes and edge labels. Graph 
    algorithms are able to store their results as attributes on the labels. Attributes can
    be accessed and set as with a dict.
    
    +--------------------+--------------------------------------------------+
    | Operations         | Description                                      |
    +====================+==================================================+
    |:code:`n[key] = val`|set the value of :code:`n[key]` to :code:`val`.   |
    +--------------------+--------------------------------------------------+
    |:code:`n[key]`      |Return the item of :code:`n` with key :code:`key`.|
    +--------------------+--------------------------------------------------+
    
    
    Parameters
    ----------
    name : string
        The label name
        
    attrs 
        Arbitrary attributes stored by the graph label.
    
    """
    def __init__(self,name,**attrs):
        self._name = name
        self._attrs = attrs
    
    def __repr__(self):
        return repr(self._name)+ " : "+repr(self._attrs)
    
    def __getitem__(self,key):
        return self._attrs[key]
    
    def __setitem__(self,key,value):
        self._attrs[key] = value
    
    @staticmethod
    def node_wrapper(node):
        """Wrap a node in a GraphLabel. Useful as the node_map for :class:`Graph.new_projection`.
        
        Parameters
        ----------
        node 
            The node to be wrapped.
        
        Returns
        -------
        GraphLabel
            A GraphLabel object with :code:`name=str(node)` and ``node`` stored as the
            attribute ``data``.
        """
        return GraphLabel(name = str(node), data = node)
        
    @staticmethod
    def edge_wrapper(src,dst,edge_obj):
        """Wrap an edge in a GraphLabel. Useful as the edge_map for :class:`Graph.new_projection`.
        
        Parameters
        ----------
        src 
            The source node of the edge (this is ignored).
            
        dst
            The destination node of the edge (this is ignored).
            
        edge_obj
            The edge_obj to be wrapped.
                    
        Returns
        -------
        GraphLabel
            A GraphLabel object with :code:`name=str(edge_obj)` and ``edge_obj`` stored as
            the attribute ``data``.
        """
        return GraphLabel(name = str(edge_obj), data = edge_obj)
        
    @property
    def name(self):
        """The name of the graph label"""
        return self._name