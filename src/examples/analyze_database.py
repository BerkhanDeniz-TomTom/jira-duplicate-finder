import pickle
import faiss
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

def analyze_database(directory='./bug_database'):
    # 1. Read metadata
    print("=== Metadata Analysis ===")
    with open(Path(directory) / 'metadata.pkl', 'rb') as f:
        metadata = pickle.load(f)
    
    df = metadata['bugs_data']
    print(f"\nTotal bugs: {len(df)}")
    print("\nStatus distribution:")
    print(df['status'].value_counts())
    
    print("\nSample bug:")
    sample_bug = df.iloc[0]
    print(f"Key: {sample_bug['key']}")
    print(f"Summary: {sample_bug['summary']}")
    print(f"Status: {sample_bug['status']}")
    print(f"Created: {sample_bug['created']}")
    
    # 2. Analyze FAISS index
    print("\n=== Vector Space Analysis ===")
    index = faiss.read_index(str(Path(directory) / 'index.faiss'))
    print(f"Number of vectors: {index.ntotal}")
    print(f"Vector dimension: {index.d}")
    
    # 3. Visualize vectors
    vectors = index.reconstruct_n(0, index.ntotal)
    pca = PCA(n_components=2)
    vectors_2d = pca.fit_transform(vectors)
    
    plt.figure(figsize=(10, 10))
    plt.scatter(vectors_2d[:, 0], vectors_2d[:, 1], alpha=0.5)
    plt.title('Bug Embeddings Visualization')
    plt.xlabel('PCA Component 1')
    plt.ylabel('PCA Component 2')
    
    output_path = Path(directory) / 'embeddings_visualization.png'
    plt.savefig(output_path)
    plt.close()  # Close the figure to free memory
    print(f"\nVisualization saved to: {output_path}")

    return metadata, index

if __name__ == "__main__":
    analyze_database()