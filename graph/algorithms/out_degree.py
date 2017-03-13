def out_degree(g):
    """Computes the out degree of each node.
    
    Parameters
    ----------
    g : :class:`graph.Graph`
        Each node in the graph should be a :class:`graph.algorithms.GraphLabel`, or else 
        behave like a dict. 
    
    """
    def emitter(src,dst,e):
        return [1],[]
    
    def collector(node,msgs):
        node['out_degree'] = len(list(msgs))
    
    g.send_collect(emitter,collector)