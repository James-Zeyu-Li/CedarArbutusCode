#!/usr/bin/env python3
import os
import json
from kg_gen import KGGen, Graph

kg_gen_model = "phi4/latest"
only_sample_first_document = True
graph_cache_file = "cached_graph.json"
test_data_dir = "./test_data"

def create_dummy_test_data(directory):
    os.makedirs(directory, exist_ok=True)
    dummy_data = [
        {"html": "This is a test content for KG generation using phi4. Extract key entities such as names and dates."},
        {"html": "Another sample text for testing KGGEN with phi4. Identify and list the main topics and objects."}
    ]
    file_path = os.path.join(directory, "dummy_data.json")
    with open(file_path, "w") as f:
        json.dump(dummy_data, f, indent=2)
    print(f"Dummy test data created at: {file_path}")

def generate_graph():
    print("Initializing KGGen with model:", kg_gen_model)
    kg = KGGen(model=kg_gen_model, api_key=os.getenv("OPENAI_API_KEY", ""))
    
    data_files = os.listdir(test_data_dir)
    graphs = []
    for i, file in enumerate(data_files):
        file_path = os.path.join(test_data_dir, file)
        print(f"Reading {i+1}/{len(data_files)}: {file_path}")
        with open(file_path, "r") as f:
            data = json.load(f)
            print(f"  Contains {len(data)} entries.")
            for j, entry in enumerate(data):
                print(f"Generating graph for entry {j+1}/{len(data)}...")
                try:
                    # 调用 KGGen 生成图谱
                    graph = kg.generate(input_data=entry["html"], context="test context")
                except Exception as e:
                    print("Error generating graph:", e)
                    continue
                graphs.append(graph)
                if only_sample_first_document:
                    print("Only sampling first document.")
                    return graph
    if graphs:
        print("Aggregating graphs...")
        aggregated_graph = kg.aggregate(graphs)
        print("Aggregation complete.")
        return aggregated_graph
    else:
        print("No graphs generated.")
        return None

def main():
    create_dummy_test_data(test_data_dir)
    
    graph = None
    if not os.path.isfile(graph_cache_file) or input("Re-generate cached graph? [y/N] ") == "y":
        graph = generate_graph()
        if graph is not None:
            with open(graph_cache_file, "w") as f:
                data = {
                    "entities": list(graph.entities),
                    "edges": list(graph.edges),
                    "relations": list(graph.relations)
                }
                json.dump(data, f, indent=2)
        else:
            print("Graph generation failed.")
            return
    else:
        with open(graph_cache_file, "r") as f:
            data = json.load(f)
        graph = Graph(
            entities = data["entities"],
            relations = data["relations"],
            edges = data["edges"],
        )
    
    if graph:
        print("Graph generated successfully!")
        print("Number of entities:", len(graph.entities))
        print("Number of relations:", len(graph.relations))
        print("Number of edges:", len(graph.edges))
    else:
        print("No graph generated.")

if __name__ == "__main__":
    main()
