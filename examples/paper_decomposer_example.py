"""
Example: Using Paper Decomposer with a sample paper.
"""

from paper_decomposer import PaperToNotebookController

def main():
    """Example usage of paper decomposer."""
    
    # Initialize controller with toy mode for fast execution
    controller = PaperToNotebookController(
        max_iterations=3,
        toy_mode=True,
        image="python:3.11-slim",
        timeout_sec=300
    )
    
    # Example 1: Process a local PDF
    print("Example 1: Processing local PDF")
    print("-" * 60)
    
    result = controller.run_from_pdf(
        "examples/sample_paper.pdf",
        experiment_index=0
    )
    
    if result["success"]:
        print(f"\n✓ Success!")
        print(f"  Notebook: {result['files']['notebook']}")
        print(f"  Executed in {result['execution']['iterations']} iterations")
        print(f"  Total time: {result['total_time']:.1f}s")
    else:
        print(f"\n✗ Failed: {result.get('error')}")
    
    # Example 2: Process from arXiv (uncomment to use)
    # print("\n\nExample 2: Processing from arXiv")
    # print("-" * 60)
    # 
    # result = controller.run_from_arxiv(
    #     "https://arxiv.org/abs/2301.12345",
    #     experiment_index=0
    # )
    
    # Example 3: Process multiple experiments
    # print("\n\nExample 3: Processing all experiments")
    # print("-" * 60)
    #
    # # First, get the decomposition
    # from paper_decomposer.ingest import extract_text_from_pdf, chunk_text
    # from paper_decomposer.decompose import decompose_paper
    #
    # text = extract_text_from_pdf("paper.pdf")
    # chunks = chunk_text(text)
    # decomposition = decompose_paper(controller.rlm_client, chunks)
    #
    # # Process each experiment
    # for i, exp in enumerate(decomposition["experiments"]):
    #     print(f"\nExperiment {i}: {exp['title']}")
    #     result = controller.run_from_pdf("paper.pdf", experiment_index=i)
    #     print(f"  Status: {'✓ Success' if result['success'] else '✗ Failed'}")


if __name__ == "__main__":
    main()
