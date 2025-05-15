from kg_gen import KGGen, Graph
import graph
import pdf
import argparse
import os
import time


# Looks for files with names in the chunk format, aggregates them, saves the
# aggregated knowledge graph
def aggregate(kg, chunks_dir):
    aggregation_fname = chunks_dir + "/aggregated.json"
    if os.path.isfile(aggregation_fname):
        print("Aggregation file already exists!")
        return

    graphs = []
    for fname in os.listdir(chunks_dir):
        if fname.startswith("chunk-"):
            print(f"Loading chunk graph '{fname}'")
            g = graph.load_graph(chunks_dir + "/" + fname)
            graphs.append(g)

    print(f"Aggregating {len(graphs)} graphs")

    aggregate_st = time.time()
    aggregated_graph = kg.aggregate(graphs)
    aggregate_en = time.time()
    aggregate_duration = aggregate_en - aggregate_st
    print(f"\tAggregation processed in {aggregate_duration:.2f}s")

    graph.save_graph(aggregated_graph, aggregation_fname)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("filename")
    parser.add_argument("-o", "--output")
    # parser.add_argument("-m", "--model", default="")
    # Aggregate after chunks processed
    parser.add_argument("-a", action="store_true")
    parser.add_argument("--only", default="")
    args = parser.parse_args()

    print(f"Reading {args.filename}")
    print(f"Outputting to {args.output}")

    print("Hello from graph-ingestion-playground!")

    pages = pdf.get_pdf_pages_text(args.filename)
    # TODO: Make it smarter
    # Maybe aggregate text until a threshold is reached, then attach sources to that
    # Not sure how to split it though, by sentences or words or characters?
    chunks = pdf.make_chunks(pages)

    # print("First three chunks")
    # for c in chunks[:3]:
    # 	print("--")
    # 	print(c)
    # print("--")

    print("Connecting to model")
    # kg = KGGen(
    #     model="ollama/phi4",
    #     api_key="",
    #     # api_base="http://localhost:11434",  # Ollama 默认地址
    #     messages_format="ollama",
    #     system_message_merge=True  # 将 system 消息合并到 user
    # )
    kg = KGGen(
        model=os.getenv("KG_GEN_MODEL", "ollama/phi4"),
        api_key=os.getenv("KG_GEN_API_KEY", ""),
    )

    for i, (entry, (st, en)) in enumerate(chunks):
        # Early termination option for testing
        if args.only != "" and args.only.isdigit() and i >= int(args.only):
            print(f"Stopping after first {args.only} chunks")
            break

        print(f"Process chunk {i+1}/{len(chunks)}")

        # Check for checkpoint
        chunk_output_path = args.output + f"/chunk-{i}-{st}-{en}.json"
        if os.path.isfile(chunk_output_path):
            print("\tSkipping due to checkpoint detection!")
            continue

        generate_st = time.time()

        try:
            kgraph = kg.generate(
                input_data=entry,
            )
        except Exception as e:
            print(f"\tError in kg.generate: {e}")
            # 创建一个空的Graph对象
            kgraph = Graph(entities=set(), relations=[], edges=set())

        generate_en = time.time()
        generate_duration = generate_en - generate_st
        print(f"\tChunk processed in {generate_duration:.2f}s")

        print(f"\tSaving as '{chunk_output_path}'")
        graph_json = graph.graph_to_json(kgraph)
        graph.save_json(graph_json, chunk_output_path)

    print(f"All chunks processed, output is in {args.output}")

    if args.a:
        print("Beginning aggregation")
        aggregate(kg, args.output)

    print("Done!")


if __name__ == "__main__":
    main()
