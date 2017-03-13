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