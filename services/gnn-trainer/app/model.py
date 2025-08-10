import torch
import torch.nn.functional as F
from torch_geometric.nn import GATv2Conv
from loguru import logger

class GNNModel(torch.nn.Module):
    def __init__(self, num_node_features: int, num_classes: int):
        super().__init__()
        logger.info(f"Initializing GNNModel with {num_node_features} features and {num_classes} classes.")
        
        # Using 2-3 GATv2Conv layers as specified
        self.conv1 = GATv2Conv(num_node_features, 128) # Output features of first layer
        self.conv2 = GATv2Conv(128, 64) # Output features of second layer
        self.conv3 = GATv2Conv(64, num_classes) # Output features of third layer, directly to num_classes

    def forward(self, data):
        x, edge_index, edge_attr = data.x, data.edge_index, data.edge_attr
        
        # Apply Graph Attention Convolution layers
        x = self.conv1(x, edge_index, edge_attr)
        x = F.relu(x)
        # Optional: Add GraphNorm here if needed, e.g., self.norm1 = GraphNorm(128)
        # x = self.norm1(x)

        x = self.conv2(x, edge_index, edge_attr)
        x = F.relu(x)
        # Optional: Add GraphNorm here if needed
        
        x = self.conv3(x, edge_index, edge_attr)
        
        # Output layer with LogSoftmax for node classification
        return F.log_softmax(x, dim=1)
