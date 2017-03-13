def connected_comp(g):
    """Computes the connected components of the graph.
    
    Each node :samp:`{node}`, in the graph should be a :class:`graph.GraphLabel`. Each
    connected component receives a distinct label, and the labels are stored in 
    :samp:`{node}['cc']`.
    
    Parameters
    ----------
    g : :class:`graph.Graph`
         Each node in the graph should be a 
        :class:`graph.algorithms.GraphLabel`, or else behave like a dict. 
    
    """
    # We initialize each node by setting node['cc'] to it's own id.
    def init_node(node):
        node['cc'] = node.name+" id:"+str(id(node))
        node['halt'] = True
    g.update_nodes(init_node) #Initialize vertices 
    
    # Each edge sends messages to both nodes informing them of the value of each other's node['cc']
    def emitter(src,dst,e):
        return [dst['cc']],[src['cc']]

    # The node sets node['cc'] to the smallest value received from it's neighbors.
    def collector(node,msg_iter):
        node['halt'] = True
        for near_cc in msg_iter:
            if near_cc < node['cc']:
                node['cc'] = near_cc
                node['halt'] = False
    
    g.send_collect(emitter,collector)
    while sum( 1 for node in g.nodes() if not node['halt'])>0:
        g.send_collect(emitter,collector)