import pandas as pd
import itertools
import pickle
import re

class Graph():    
    """Creates a graph with the specified vertices and edges
    
    Parameters
    ----------
    edges : iterable, optional
        An interable which yields objects of type :class:`graph.Edge`.
    nodes : set-like, optional
        A collection of (distinct) hashable objects.
    """
    def __init__(self,edges = None, nodes = None):
        #self.nodes = pd.DataFrame(columns = ['nodes'])
        #self.edges = pd.DataFrame(columns = ['src_node','dst_node','property'])
        self.nodes = set()
        if edges is not None:
            self.add_edges(edges)
        if nodes is not None:
            self.add_nodes(nodes)
    
    def from_df(self,edges):
        self.edges = edges
#         self.nodes = nodes.append(
#                             edges[['src_node']].rename(columns = {'src_node':'nodes'})).append(
#                             edges[['dst_node']].rename(columns = {'dst_node':'nodes'})).drop_duplicates()
        self.nodes = {node for node in edges.src_node}|{node for node in edges.dst_node}
        return self
    
    def __getitem__(self, key):
        """Returns the adjacency list for the specified vertex
        
        Parameters
        ----------
        key : pair of indices
        """
        return True
        
    def add_nodes(self,nodes):
        """Adds nodes to the graph.
        
        Parameters
        ----------
        nodes : set-like
            A collection of (distinct) hashable objects.
        """
        #new_nodes = pd.DataFrame({'nodes':list(nodes)})
        #self.nodes = self.nodes.append(new_nodes).drop_duplicates()
        self.nodes.update(nodes)
        
    def add_edges(self,edges):
        """Adds edges to the graph. Any new source and destination nodes are also added.
        
        Parameters
        ----------
        edges : iterable
            An iterable which yields objects of type :class:`graph.Edge`.
        """
        #new_edges = pd.DataFrame(columns = ['src_node','dst_node','property'], data = [[e.src,e.dst,e.properties] for e in edges])
        new_edges = pd.DataFrame(columns = ['src_node','dst_node','edge_obj'], data = [[src,dst,e.edge_obj] for src,dst,edge_obj in edges])
        self.edges = self.edges.append(new_edges)
        self.add_nodes([e.src for e in edges]+[e.dst for e in edges])
    
    def subgraph(self, edge_pred = None,node_pred = None):
        """Returns the maximal subgraph for which all nodes satisfy the node predicate
        and all edges satisfy the edge predicate.
        
        Parameters
        ----------
        node_pred : function, optional
            This should be a function of one argument which returns a :code:`bool`.
            The default value of :code:`None` means all nodes are included
            
        node_pred : function, optional
            This should be a function of one argument which returns a :code:`bool`.
            The default value of :code:`None` means all edges are included whose source and 
            destination nodes satisfy the node predicate.
        
        """
        if node_pred == None:
            node_pred = lambda x: True
        if edge_pred == None:
            edge_pred = lambda x: True
            
        edge_mask = (self.edges.apply(lambda x: (edge_pred(x.src_node,x.dst_node,x.edge_obj)),axis = 1)) \
                      & (self.edges.src_node.apply(node_pred)) \
                      & (self.edges.dst_node.apply(node_pred))
                      
        edges = self.edges[edge_mask]
        new_graph = Graph().from_df(edges)
        new_graph.add_nodes({node for node in self.nodes if node_pred(node)})
        return new_graph
        #return Graph().from_df(edges,self.nodes[self.nodes['nodes'].apply(node_pred)])
                    
    def send_collect(self, emmiter, collector):
        """Request each edge triple to emmit messages which will be delivered to its source and destination node.
        
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
            
            +--------------------+--------------------+
            |Return Values       |Description         |
            +====================+====================+
            |:code:`src_msg_iter`|An iterator which   |
            |                    |yields messages     |
            |                    |delivered to the    |
            |                    |source node         |
            +--------------------+--------------------+
            |:code:`src_msg_iter`|An iterator which   |
            |                    |yields messages     |
            |                    |delivered to the    |
            |                    |destination node    |
            +--------------------+--------------------+
            
        collector : function
            This should be a function of the form:
            
            :code:`collector(node,msg_iter)`
            
            +-------------------------+--------------------+
            |Parameters               |Description         |
            +=========================+====================+
            |:code:`node`             |The recipient node  |
            +-------------------------+--------------------+
            |:code:`msg_iter`         |An iterator of      |
            |                         |messages addressed  |
            |                         |to the node         |
            +-------------------------+--------------------+
            
            +--------------------+
            |Return Values       |
            +====================+
            |:code:`None`        |
            +--------------------+
            
            
        
        """
        #outputs = itertools.chain.from_iterable( emmiter(e) for e in Edge.from_df(self.edges))
        #outputs = itertools.chain.from_iterable( emmiter(e) for e in Edge.from_df(self.edges))
        
        # Attach addresses to the messages:
        addressed_msgs = itertools.chain.from_iterable(zip((e.src_node,e.dst_node),
                    emmiter(e.src_node,e.dst_node,e.edge_obj))
                    for e in self.edges.itertuples())
        #agg_msgs = dict()
        #for node,msg in outputs:
        #    agg_msgs[node] = msg if node not in agg_msgs else agg_msgs[node]+msg
        
        #Aggregate the messages to each node
        agg_msgs = dict()
        for node,msg_iter in addressed_msgs:
           agg_msgs[node] = msg_iter if node not in agg_msgs \
                            else itertools.chain(agg_msgs[node],msg_iter)
        for node in self.nodes:
            collector(node,agg_msgs.get(node,[]))
    
    def map_nodes(self,map):
        for node in self.nodes:
            map(node)
    
    def map_edges(self,map):
        for e in self.edges.itertuples():
            map(e.src_node,e.dst_node,e.edge_obj)
    
    def project_a_copy(self,edge_map,node_map):
        processed_node_objs = {}
        for node in self.nodes:
            processed_node_objs[node]=node_map(node)
        new_edges = pd.DataFrame({'src_node':self.edges.src_node.apply(lambda x: processed_node_objs[x]),
                                  'dst_node':self.edges.dst_node.apply(lambda x: processed_node_objs[x]),
                                  'edge_obj':self.edges.edge_obj.apply(edge_map)}) 
        new_graph = Graph().from_df(new_edges)
        new_graph.add_nodes(processed_node_objs.values())
        return new_graph
                
    def __repr__(self):
        return repr(self.nodes)+'\n'+repr(self.edges)
    
    def save(self,filename):
        with open(filename,'wb') as file:
            pickle.dump({'nodes':self.nodes,'edges':self.edges},file)
    
    def find(self,motif):
        patterns = [p.strip() for p in motif.split(';')]
        def parse_pattern(p):
            a = re.search('\(.*\)-',p)
            src = '' if not a else a.group(0)[1:-2].strip()
            e = re.search('-\[.*\]->',p)
            e = '' if not e else e.group(0)[2:-3].strip()
            b = re.search('->\(.*\)',p)
            dst = '' if not b else b.group(0)[3:-1].strip()
            return src,dst,e
        
        df_out = pd.DataFrame()
        for p in patterns:
            src,dst,e = parse_pattern(p)
            mask = self.edges
            data = dict()
            if src != '':
                data[src] = self.edges.src_node
            if dst != '':
                data[dst] = self.edges.dst_node
            if e != '':
                data[e] = self.edges.edge_obj
            df_tmp = pd.DataFrame(data)
            if df_out.size == 0:
                df_out = df_tmp
            else:
                df_out = df_out.merge(df_tmp,how='inner')
        return df_out
    
    @staticmethod
    def load(filename):
        with open(filename,'rb') as file:
            data = pickle.load(file)
            new_graph = Graph().from_df(data['edges'])
            new_graph.add_nodes(data['nodes'])
        return new_graph
        
class GraphObj():
    def __init__(self,name,**attrs):
        self.name = name
        self.attrs = attrs
    
    def __repr__(self):
        return repr(self.name)+ " : "+repr(self.attrs)
    
    def __getitem__(self,key):
        return self.attrs[key]
    
    def __setitem__(self,key,value):
        self.attrs[key] = value

# class GraphObj(dict):
#     def __init__(self,name,**attrs):
#         self.name = name
#         super().__init__(attrs)
#         
#     def __repr__(self):
#         return repr(self.name)+" : "+super().__repr__()

# class Vertex():
#     """A vertex"""
#     def __init__(self,id,**attrs):
#         """Create a vertex with the specified id and attributes."""
#         self.attrs = attrs
#         
#     def in_degee(self):
#         """Returns the number of incoming edges to the vertex
#         
#         Returns
#         -------
#         int
#             The number of incoming edges.
#         """
#         return 5
        

# class Edge():
#     """A Generic Edge.
#     
#     Parameters
#     ----------
#     src_node : Object
#         The node at the source of the edge.
#     dst_node : Object
#         The node at the target of the edge.
#     properties : Object
#         A python object attached to the edge.
#     """
#     def __init__(self,src_node,dst_node,properties):
#         self._src_node = src_node
#         self._dst_node = dst_node
#         self._properties = properties
#     
#     @staticmethod
#     def from_df(edges):
#         converted = edges.apply(lambda x: Edge(x[0],x[1],x[2]), axis = 1)
#         for e in converted:
#             yield e
#         
#     @property
#     def properties(self):
#         """Returns the properties attached to the edge.
#         
#         Returns
#         -------
#         Object
#             Returns the properties attached to the edge.
#         """
#         return self._properties
#     
#     @property
#     def src(self):
#         """Returns the node at the source of the edge.
#         
#         Returns
#         -------
#         Object
#             Returns the node which sits at the source of the edge.
#         """
#         return self._src_node
#     
#     @property
#     def dst(self):
#         """Returns the node at the destination of the edge.
#         
#         Returns
#         -------
#         Object
#             Returns the node which sits at the destination of the edge.
#         """
#         return self._dst_node
#         
#     def __repr__(self):
#         return 'src: ' + repr(self.src) + ' edge: ' + repr(self.properties) + ' dst: ' + repr(self.dst)
        