# coding:utf-8
import pygraphviz as pgv


def draw_director_tree(node_map, pairs, save_path):
    tree_graph = pgv.AGraph(directed=True, strict=True, encoding='UTF-8')
    tree_graph.node_attr['style'] = 'filled'
    tree_graph.node_attr['shape'] = 'square'

    for node_id, node_name in node_map.items():
        tree_graph.add_node(node_id, label=node_name)
    for f_id, s_id in pairs:
        tree_graph.add_edge(f_id, s_id)
    tree_graph.graph_attr['epsilon'] = '0.001'
    # print tree_graph.string()  # print dot file to standard output
    # tree_graph.write('director_tree.dot')
    tree_graph.layout('dot')  # layout with dot
    tree_graph.draw(save_path)
