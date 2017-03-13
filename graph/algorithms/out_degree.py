def out_degree(g):
    """Computes the out degree of each node.
    
    Parameters
    ----------
    g : :class:`graph.Graph`
        Each node in the graph should be a :class:`graph.algorithms.GraphLabel`, or else 
        behave like a dict. 
    
    """
    # Each edge emits a non-empty message to the source node (and an empty message to the destination node)
    def emitter(src,dst,e):
        return [1],[]
    
    # Each node collects all the messages it receives and counts them, the result is the number of outgoing edges.
    def collector(node,msgs):
        node['out_degree'] = len(list(msgs))
    
    g.send_collect(emitter,collector)