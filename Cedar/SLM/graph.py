import json
from kg_gen import Graph
import os


def graph_to_json(graph):
	data = {
		"entities": list(graph.entities),
		"edges": list(graph.edges),
		"relations": list(graph.relations),
	}
	return data


def graph_from_json(data):
	graph = Graph(
		entities = data["entities"],
		relations = data["relations"],
		edges = data["edges"],
	)
	return graph


def save_json(data, path):
	os.makedirs(os.path.dirname(path), exist_ok=True)
	with open(path, "w") as f:
		json.dump(data, f, indent=2)


def save_graph(graph, path):
	data = graph_to_json(graph)
	save_json(data, path)


def load_graph(path):
	graph = None
	with open(path, "r") as file:
		data = json.load(file)
		graph = graph_from_json(data)
	return graph