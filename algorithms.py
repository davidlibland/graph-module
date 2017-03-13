from graph import *
        
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
        
def connected_comp(g):
    """Computes the connected components of the graph.
    
    Each node :samp:`{node}`, in the graph should be a :class:`graph.GraphLabel`. Each
    connected component receives a distinct label, and the labels are stored in 
    :samp:`{node}['cc']`.
    
    Parameters
    ----------
    g : :class:`graph.Graph`
        Each node in the graph should be a :class:`graph.GraphLabel`. 
    
    """
    def init_node(node):
        node['cc'] = node.name+" id:"+str(id(node))
        node['halt'] = True
    g.update_nodes(init_node) #Initialize vertices 
    
    def emitter(src,dst,e):
        return [dst['cc']],[src['cc']]

    def collector(node,msg_iter):
        node['halt'] = True
        for near_cc in msg_iter:
            if near_cc < node['cc']:
                node['cc'] = near_cc
                node['halt'] = False
    
    g.send_collect(emitter,collector)
    while sum( 1 for node in g.nodes() if not node['halt'])>0:
        g.send_collect(emitter,collector)
        
def out_degree(g):
    def emitter(src,dst,e):
        return [1],[]
    
    def collector(node,msgs):
        node['out_degree'] = len(list(msgs))
    
    g.send_collect(emitter,collector)
    

def page_rank(g,reset_prob,threshold=0.001):
    """Computes the PageRank of each node and stores it in node['page_rank'].
    
    Note
    ----
    The node and edge objects must be able to store attributes in dict-like fashion. 
    If necessary you can use the method g.new_projection(edge_map,node_map)
    where 
    
    Parameters
    ----------
    g : graph.Graph
        The graph we use to compute the PageRank
        
    reset_prob : float
        The probability (between 0 and 1) that one jumps to a random node (as opposed to 
        following one of the outgoing edges).
    
    threshold : float,optional
        The algorithm terminates when the PageRank of each node has converged up to this
        threshold. This must be a postive number.
    """
    if not (reset_prob >= 0  and reset_prob <=1):
        raise ValueError('We require 0 <= reset_prob <= 1')
        
    if not threshold > 0:
        raise ValueError('We require 0 < threshold')
        
    #Initialize the nodes and edges:
    out_degree(g) # make sure each node knows it's out_degree
    
    #Each node starts the algorithm with a PageRank of 1.
    def init_node(node):
        node['page_rank'] = 1.
        node['halt'] = False
    g.update_nodes(init_node)
    
    #Each edge remember the proportion of the traffic if carries out of it's source:
    def init_edge(src,dst,e):
        e['traffic_prop'] = 1./src['out_degree']
    g.update_edges(init_edge)
    
    #The emitter sends the relevant proportion of the 
    #source node's page_rank along each edge:
    def emitter(src,dst,e):
        return [],[src['page_rank']*e['traffic_prop']]
        
    

    #Dangling nodes (nodes with out_degree==0) cannot transmit it's current page_rank
    #along any outgoing edges, so we need to collect their current page_ranks centrally
    #and redistibute them equally amongst all nodes.
    num_nodes = sum(1 for node in g.nodes())
    
    node_pred = lambda node : node['out_degree']==0
    dangling_nodes = g.new_subgraph(node_pred=node_pred).nodes()
    
    def page_rank_collector(node,incoming_ranks,avg_dangle_rank):
        old_rank = node['page_rank']
        node['page_rank'] = (1-reset_prob)*(sum(incoming_ranks)+avg_dangle_rank)+reset_prob  
        if abs(old_rank - node['page_rank']) < threshold:
            node['halt']=True
        else:
            node['halt']=False
    
    while sum( 1 for node in g.nodes() if not node['halt']) > 0:
        avg_dangle_rank = sum(node['page_rank'] for node in dangling_nodes)/num_nodes
        collector = lambda node,msgs: page_rank_collector(node,msgs,avg_dangle_rank)
        g.send_collect(emitter,collector)




