import pandas as pd
import itertools
import pickle
import re

class Graph():    
    """Creates a graph with the specified vertices and edges
    
    Parameters
    ----------
    edges : iterable, optional
        An iterable which yields triples of the form
        :code:`(src_node,dst_node,edge_obj)`
        signifying a directed edge whose source is :code:`src_node` and whose 
        destination is :code:`dst_node`. The object :code:`edge_obj` will be 
        attached to this edge (as a label).
    nodes : set-like, optional
        A collection of (distinct) hashable objects.
        
    Example
    --------
    
    .. code-block:: python
        :linenos:
        
        g = Graph(edges = [('A','B',1),('A','C',1),
                           ('B','C',1),('C','D',1),('D','A',1)],
                  nodes = {'E'})
        
    produces the graph :code:`g`:
    
    .. image:: graph1.png
    
    """
    def __init__(self,edges = None, nodes = None):
        self._nodes = set()
        self._edges = pd.DataFrame(columns = ['src_node','dst_node','edge_obj'])
        if edges is not None:
            self.add_edges(edges)
        if nodes is not None:
            self.add_nodes(nodes)
    
    def from_df(self,edges):
        self._edges = edges
        self._nodes = {node for node in edges.src_node}|{node for node in edges.dst_node}
        return self
        
    def add_nodes(self,nodes):
        """Adds nodes to the graph.
        
        Parameters
        ----------
        nodes : set-like
            A collection of (distinct) hashable objects.
        """
        self._nodes.update(nodes)
        
    def add_edges(self,edges):
        """Adds edges to the graph. Any new source and destination nodes are also added.
        
        Parameters
        ----------
        edges : iterable
            An iterable which yields triples of the form
            :code:`(src_node,dst_node,edge_obj)`
            signifying a directed edge whose source is :code:`src_node` and whose 
            destination is :code:`dst_node`. The object :code:`edge_obj` will be 
            attached to this edge (as a label).
            
        """
        new_edges = pd.DataFrame(columns = ['src_node','dst_node','edge_obj'],
                                 data = [[src,dst,edge_obj] for src,dst,edge_obj in edges])
        self._edges = self._edges.append(new_edges)
        self.add_nodes({node for node in new_edges.src_node}|
                       {node for node in new_edges.dst_node})
    
    def new_subgraph(self, edge_pred = None,node_pred = None):
        """Returns the maximal subgraph for which all nodes satisfy the node predicate
        and all edges satisfy the edge predicate.
        
        Parameters
        ----------
        node_pred : function, optional
            This should be a function of one argument which returns a :code:`bool`.
            If :code:`node_pred` is ommitted, then all nodes are included.
            
        node_pred : function, optional
            This should be a function of one argument which returns a :code:`bool`.
            If :code:`edge_pred` is ommitted, all edges are included whose source and 
            destination nodes satisfy the node predicate.
        
        Returns
        -------
        :class:`graph.Graph`
            The maximal subgraph satisfying the given predicates.
        
        Example
        -------
        .. code-block:: python
            :linenos:
        
            g = Graph(edges = [('A','B',1),('A','C',1),
                               ('B','C',2),('C','D',2),('D','A',3)],
                      nodes = {'E'})
            edge_pred = (lambda src,dst,e: e==2)
            node_pred = (lambda node: node in {'A','B','C'})
            h = g.subgraph(edge_pred = edge_pred,node_pred = node_pred)
            
        produces the subgraph :code:`h`:
        
        .. image:: graph2.png
        
        of the graph :code:`g`:
    
        .. image:: graph1.png
        """
        if node_pred == None:
            node_pred = lambda x: True
        if edge_pred == None:
            edge_pred = lambda x,y,z: True
            
        edge_mask = (self._edges.apply(lambda x: (edge_pred(x.src_node,x.dst_node,x.edge_obj)),
                                       axis = 1)) \
                    & (self._edges.src_node.apply(node_pred)) \
                    & (self._edges.dst_node.apply(node_pred))
                      
        edges = self._edges[edge_mask]
        new_graph = Graph().from_df(edges)
        new_graph.add_nodes({node for node in self._nodes if node_pred(node)})
        return new_graph
                    
    def send_collect(self, emmiter, collector):
        """Request each edge triple to emmit messages via the function :code:`emitter`
         which will be delivered to its source and destination node where they will be
         processed by the function :code:`collector`.
        
        Parameters
        ----------
        emitter : function
            This should be a function of the form:
            
            :code:`emitter(src_node,dst_node,edge_obj) -> src_msg_iter,dst_msg_iter`
            
            +-------------------------+--------------------+
            |Parameters               |Description         |
            +=========================+====================+
            |:code:`src_node`         |the source node     |
            +-------------------------+--------------------+
            |:code:`dst_node`         |the destination node|
            +-------------------------+--------------------+
            |:code:`edge_obj`         |the object attached |
            |                         |to the edge         |
            +-------------------------+--------------------+
            |**Return Values**        |                    |
            +-------------------------+--------------------+
            |:code:`src_msg_iter`     |An iterator which   |
            |                         |yields messages     |
            |                         |delivered to the    |
            |                         |source node         |
            +-------------------------+--------------------+
            |:code:`src_msg_iter`     |An iterator which   |
            |                         |yields messages     |
            |                         |delivered to the    |
            |                         |destination node    |
            +-------------------------+--------------------+
            
        collector : function
            This should be a function of the form :code:`collector(node,msg_iter)`
            which processes the messages in :code:`msg_iter` and modifies :code:`node`
            acordingly. Any return values will be ignored.
            
            +-------------------------+--------------------+
            |Parameters               |Description         |
            +=========================+====================+
            |:code:`node`             |The recipient node  |
            +-------------------------+--------------------+
            |:code:`msg_iter`         |An iterator of      |
            |                         |messages addressed  |
            |                         |to the node         |
            +-------------------------+--------------------+
            
        
        """
        
        # Attach addresses to the messages:
        addressed_msgs = itertools.chain.from_iterable(zip((e.src_node,e.dst_node),
                    emmiter(e.src_node,e.dst_node,e.edge_obj))
                    for e in self._edges.itertuples())
        
        # Aggregate the messages to each node
        agg_msgs = dict()
        for node,msg_iter in addressed_msgs:
           agg_msgs[node] = msg_iter if node not in agg_msgs \
                            else itertools.chain(agg_msgs[node],msg_iter)
        
        # Collect the messages
        for node in self._nodes:
            collector(node,agg_msgs.get(node,[]))
    
    def update_nodes(self,updater):
        """Apply the function :code:`updater(node)` to each node.
        
        Parameters
        ----------
        updater : function
            This should be a function of the form :code:`updater(node)`
            which modifies :code:`node`. Any return values will be ignored.
            
            +-------------------------+------------------------+
            |Parameters               |Description             |
            +=========================+========================+
            |:code:`node`             |The node to be modified |
            +-------------------------+------------------------+
        """
        for node in self._nodes:
            updater(node)
    
    def update_edges(self,updater):
        """Apply the function :code:`updater(src_node,dst_node,edge_obj)` to each edge
        triple, it should treat the source and destination objects, :code:`src_node` and 
        :code:`dst_node`, as constant inputs.
        
        Parameters
        ----------
        updater : function
            This should be a function of the form :code:`updater(src_node,dst_node,edge_obj)`
            which modifies :code:`edge_obj`, while treating :code:`src_node` and 
            :code:`dst_node` as constant. Any return values will be ignored.
            
            +-------------------------+-----------------------------------------+
            |Parameters               |Description                              |
            +=========================+=========================================+
            |:code:`src_node`         |The node at the source of the edge       |
            +-------------------------+-----------------------------------------+
            |:code:`dst_node`         |The node at the destination of the edge  |
            +-------------------------+-----------------------------------------+
            |:code:`edge_obj`         |The object attached to the edge          |
            +-------------------------+-----------------------------------------+
        """
        for e in self._edges.itertuples():
            updater(e.src_node,e.dst_node,e.edge_obj)
    
    def new_projection(self,edge_map,node_map):
        """Construct a new :class:`graph.Graph` whose nodes are the values returned by 
        applying the function :code:`node_map(node) -> new_node` to each node; 
        and whose edges are the values returned by applying the function
        :code:`edge_map(src_node,dst_node,edge_obj) -> new_edge_obj` to each edge triple.
        
        Parameters
        ----------
        node_map : function
            This should be a function of the form :code:`map(src_node,dst_node,edge_obj)`
            which modifies :code:`edge_obj`, while treating :code:`src_node` and 
            :code:`dst_node` as constant. Any return values will be ignored.
            
            +-------------------------+-----------------------------------------+
            |Parameters               |Description                              |
            +=========================+=========================================+
            |:code:`node`             |The input node                           |
            +-------------------------+-----------------------------------------+
            |**Return Values**        |                                         |
            +-------------------------+-----------------------------------------+
            |:code:`new_node`         |The node created in the new graph        |
            +-------------------------+-----------------------------------------+
            
        edge_map : function
            This should be a function of the form :code:`map(src_node,dst_node,edge_obj)`
            which modifies :code:`edge_obj`, while treating :code:`src_node` and 
            :code:`dst_node` as constant. Any return values will be ignored.
            
            +-------------------------+-----------------------------------------+
            |Parameters               |Description                              |
            +=========================+=========================================+
            |:code:`src_node`         |The node at the source of the edge       |
            +-------------------------+-----------------------------------------+
            |:code:`dst_node`         |The node at the destination of the edge  |
            +-------------------------+-----------------------------------------+
            |:code:`edge_obj`         |The object attached to the edge          |
            +-------------------------+-----------------------------------------+
            |**Return Value**         |                                         |
            +-------------------------+-----------------------------------------+
            |:code:`new_edge_obj`     |The object attached to the edge created  |
            |                         |in the new graph whose source node is    | 
            |                         |:code:`node_map(src_node)` and whose     |
            |                         |destination is :code:`node_map(dst_node)`|
            +-------------------------+-----------------------------------------+
        
        Returns
        -------
        :class:`graph.Graph`
            The new graph.
        """
        processed_nodes = {}
        edge_map_variant = lambda x:edge_map(x.src_node,x.dst_node,x.edge_obj)
        for node in self._nodes:
            processed_nodes[node]=node_map(node)
        new_edges = pd.DataFrame({'src_node':self._edges.src_node.apply(processed_nodes.get),
                                  'dst_node':self._edges.dst_node.apply(processed_nodes.get),
                                  'edge_obj':self._edges.apply(edge_map_variant,axis=1)}) 
        new_graph = Graph().from_df(new_edges)
        new_graph.add_nodes(processed_nodes.values())
        return new_graph
                
    def nodes(self):
        """Returns a set-like object containing the nodes in the graph. This can be chained
        after :class:`graph.new_subgraph` to form more complex queries.
        
        Returns
        -------
        set-like
            A set-like object containing the nodes in the graph.
        """
        
        return self._nodes.copy()
    
    def find(self,motif):
        """Returns all structure patterns found in the graph which match the given motif.
        This can be chained after :class:`graph.new_subgraph` to form more complex queries.
        
        Parameters
        ----------
        motif : string
            A semi-colon separated string of structural patterns of the form 
            :samp:`({a})-[{e}]->({b})`. This structural pattern represents an edge where 
            :samp:`({a})` and :samp:`({b})` represent the source and destination nodes (these 
            can optionally be left blank) and :samp:`[{e}]` represents the object labeling 
            the edge (it can optionally be left blank).
            
            Each of :samp:`{a}`, :samp:`{b}`, and :samp:`{e}` are arbitrary substrings (they
            can optionally be left blank, and must not include the special characters
             ``()[]->``), if they are not blank, they will be used as column labels in the
            returned DataFrame.
            
        
        Returns
        -------
        DataFrame-like
            A DataFrame-like object whose columns are labelled by the distinct substrings
             :samp:`({a})`, :samp:`({b})`, :samp:`[{e}]` found among the structural pattern
             parts of the motif (the parentheses ``()`` square brackets ``[]`` are included
             to distinguish columns representing edges and nodes).
             
             Each row corresponds to a valid assignment of the node labels :samp:`({a})` and
             :samp:`({b})` to nodes in the graph, and edge labels :samp:`[e]` to edges in 
             the graph, which is consistent with *all* the structural patterns in the motif.
             For example the motif ``(a)-[e1]->(b); (b)-[e2]->(c)`` would find pairs of
             edges from ``a`` to ``b`` to ``c``. Similarly, the motif 
             ``(a)-[e1]->(b); (b)-[e2]->(a)`` would find pairs of nodes ``a`` and ``b`` 
             connected by edges in either direction.
             
        Example
        -------
        Given the graph :code:`g`:
        
        .. image:: graph1.png
        
        the query :code:`g.find("(a)-[e1]->(b); (b)-[e2]->(c)")` returns
        
        +----+-------+-------+--------+-------+--------+
        |    | \(a\) | \(b\) |  [e1]  | \(c\) |  [e2]  |
        +====+=======+=======+========+=======+========+
        |  0 | A     | B     |      1 | C     |      2 |
        +----+-------+-------+--------+-------+--------+
        |  1 | A     | C     |      1 | D     |      2 |
        +----+-------+-------+--------+-------+--------+
        |  2 | B     | C     |      2 | D     |      2 |
        +----+-------+-------+--------+-------+--------+
        |  3 | C     | D     |      2 | A     |      3 |
        +----+-------+-------+--------+-------+--------+
        |  4 | D     | A     |      3 | B     |      1 |
        +----+-------+-------+--------+-------+--------+
        |  5 | D     | A     |      3 | C     |      1 |
        +----+-------+-------+--------+-------+--------+
        
        """ 
        patterns = [p.strip() for p in motif.split(';')]
        def parse_pattern(p):
            a = re.search('\(.*\)-',p)
            src = '' if not a else a.group(0)[:-1].strip()
            e = re.search('-\[.*\]->',p)
            e = '' if not e else e.group(0)[1:-2].strip()
            b = re.search('->\(.*\)',p)
            dst = '' if not b else b.group(0)[2:].strip()
            return src,dst,e
        
        df_out = pd.DataFrame()
        for p in patterns:
            src,dst,e = parse_pattern(p)
            mask = self._edges
            data = dict()
            if src != '':
                data[src] = self._edges.src_node
            if dst != '':
                data[dst] = self._edges.dst_node
            if e != '':
                data[e] = self._edges.edge_obj
            df_tmp = pd.DataFrame(data)
            if df_out.size == 0:
                df_out = df_tmp
            else:
                df_out = df_out.merge(df_tmp,how='inner')
        return df_out
        
    def __repr__(self):
        return repr(self._nodes)+'\n'+repr(self._edges)
    
    def write_dot(self,filename,edge_repr=None,node_repr=None):
        with open(filename,'w') as file:
            file.write('digraph {\n')
            written_nodes = set()
            for e in self._edges.itertuples():
                src_txt = repr(e.src_node) if not node_repr else node_repr(e.src_node)
                dst_txt = repr(e.dst_node) if not node_repr else node_repr(e.dst_node)
                e_txt = repr(e.edge_obj) if not edge_repr else edge_repr(e.edge_obj)
                file.write('\t'+src_txt+' -> '+dst_txt+' [label="'+e_txt+'"];\n')
                written_nodes.add(e.src_node)
                written_nodes.add(e.dst_node)
            for node in (self._nodes - written_nodes):
                node_txt = repr(node) if not node_repr else node_repr(node)
                file.write('\t'+node_txt+';\n')
                
            
            file.write('}')
        
    def save(self,filename):
        with open(filename,'wb') as file:
            pickle.dump({'nodes':self._nodes,'edges':self._edges},file)
    
    @staticmethod
    def load(filename):
        with open(filename,'rb') as file:
            data = pickle.load(file)
            new_graph = Graph().from_df(data['edges'])
            new_graph.add_nodes(data['nodes'])
        return new_graph


        