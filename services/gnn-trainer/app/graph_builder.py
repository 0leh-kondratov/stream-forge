import torch
from torch_geometric.data import Data
from loguru import logger
import numpy as np

def build_pyg_graph(node_features: dict, edge_weights: dict):
    """
    Builds a PyTorch Geometric Data object from node features and edge weights.
    node_features: dict where keys are symbols and values are lists of features.
    edge_weights: dict where keys are (symbol1, symbol2) tuples and values are correlation weights.
    """
    logger.info("Building PyTorch Geometric graph...")

    if not node_features:
        logger.error("No node features provided to build graph.")
        return None

    # Map symbols to integer indices
    symbol_to_idx = {symbol: i for i, symbol in enumerate(node_features.keys())}
    num_nodes = len(symbol_to_idx)
    num_node_features = len(list(node_features.values())[0]) if node_features else 0

    if num_node_features == 0:
        logger.error("Node features are empty.")
        return None

    # Create node feature matrix (x)
    x = torch.tensor([node_features[symbol] for symbol in symbol_to_idx.keys()], dtype=torch.float)

    # Create edge index and edge attributes
    edge_index = []
    edge_attr = []
    for (s1, s2), weight in edge_weights.items():
        if s1 in symbol_to_idx and s2 in symbol_to_idx:
            edge_index.append([symbol_to_idx[s1], symbol_to_idx[s2]])
            edge_attr.append(weight)
    
    if not edge_index:
        logger.warning("No edges found to build graph.")
        # Create a graph with no edges if no edges are found, or handle as error
        edge_index = torch.empty((2, 0), dtype=torch.long)
        edge_attr = torch.empty((0), dtype=torch.float)
    else:
        edge_index = torch.tensor(edge_index, dtype=torch.long).t().contiguous()
        edge_attr = torch.tensor(edge_attr, dtype=torch.float)

    # Create PyG Data object
    data = Data(x=x, edge_index=edge_index, edge_attr=edge_attr)
    
    logger.info(f"PyG graph built with {num_nodes} nodes and {data.num_edges} edges.")
    return data
