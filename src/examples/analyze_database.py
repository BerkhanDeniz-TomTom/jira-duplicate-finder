import pickle
import faiss
import numpy as np
import pandas as pd
import os
import sys
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

def get_latest_database(base_dir) -> str:
        if not os.path.exists(base_dir):
            raise ValueError("No database directory found")
            
        databases = [d for d in os.listdir(base_dir) if d.startswith('db_')]
        if not databases:
            raise ValueError("No databases found")
            
        return os.path.join(base_dir, sorted(databases, reverse=True)[0])

def analyze_database(directory='./bug_database'):
    # Get database path from command line argument or use latest
    if len(sys.argv) > 1:
        db_name = sys.argv[1]
        db_path = os.path.join(directory, db_name)
        if not os.path.exists(db_path):
            print(f"Error: Database '{db_path}' not found")
            return
    else:
        try:
            db_path = get_latest_database(directory)
            print(f"\nUsing latest database: {db_path}")
        except ValueError as e:
            print(f"Error: {e}")
            return

    # 1. Read metadata
    print("=== Metadata Analysis ===")
    with open(Path(db_path) / 'metadata.pkl', 'rb') as f:
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
    index = faiss.read_index(str(Path(db_path) / 'index.faiss'))
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
    
    output_path = Path(db_path) / 'embeddings_visualization.png'
    plt.savefig(output_path)
    plt.close()  # Close the figure to free memory
    print(f"\nVisualization saved to: {output_path}")

    return metadata, index

if __name__ == "__main__":
    analyze_database()