import asyncio
import torch
import torch.nn.functional as F
from loguru import logger
import time # For simulating time
import numpy as np # For dummy data

from app import config
from app.telemetry import TelemetryProducer
from app.metrics import training_epochs_completed, training_loss, model_saved_total
from app.binance_client import BinanceClient
from app.feature_generator import calculate_node_features, calculate_edge_weights
from app.graph_builder import build_pyg_graph
from app.model import GNNModel
from minio import Minio # Re-import Minio for save_model_to_minio

async def load_and_prepare_data(binance_client: BinanceClient, telemetry: TelemetryProducer):
    """
    Loads data from Binance, calculates features, and builds the graph.
    """
    logger.info("Loading and preparing data...")
    await telemetry.send_status_update(status="loading", message="Collecting data from Binance.")

    # 1. Get all trading pairs
    trading_pairs = await binance_client.get_all_trading_pairs(quote_asset='USDT')
    if not trading_pairs:
        logger.error("No trading pairs found.")
        return None, None

    # For demonstration, let's limit to a few pairs to avoid excessive API calls
    # In a real scenario, you'd process all relevant pairs
    selected_pairs = trading_pairs[:5] # Example: process first 5 pairs

    all_klines_data = {}
    all_order_book_data = {}
    all_funding_rates = {}
    
    node_features_dict = {}

    for symbol in selected_pairs:
        # Get K-lines
        klines = await binance_client.get_klines(symbol=symbol, interval='1h', limit=200)
        all_klines_data[symbol] = klines

        # Get Order Book
        order_book = await binance_client.get_order_book(symbol=symbol, limit=20)
        all_order_book_data[symbol] = order_book

        # Get Funding Rate (assuming futures symbols for this)
        # For spot pairs, funding rate will be None
        funding_rate = await binance_client.get_funding_rate(symbol=symbol)
        all_funding_rates[symbol] = funding_rate

        # Calculate node features for each symbol
        features = calculate_node_features(klines, order_book, funding_rate)
        if features:
            node_features_dict[symbol] = features
        else:
            logger.warning(f"Skipping {symbol} due to insufficient data for feature calculation.")

    # Calculate edge weights (correlations)
    edge_weights = calculate_edge_weights(all_klines_data)

    # Build PyG graph
    graph_data = build_pyg_graph(node_features_dict, edge_weights)
    
    await telemetry.send_status_update(status="loading", message="Data loaded and graph built.")
    return graph_data, node_features_dict # Return node_features_dict for class mapping


async def train_gnn_model_orchestrator(stop_event: asyncio.Event, telemetry: TelemetryProducer):
    """
    Orchestrates the GNN training process: data collection, feature generation,
    graph building, model training, and model saving.
    """
    logger.info("Starting GNN model training orchestrator...")
    
    binance_client = None
    try:
        # Initialize Binance Client
        binance_client = BinanceClient(api_key=os.getenv("BINANCE_API_KEY"), api_secret=os.getenv("BINANCE_API_SECRET"))

        # 1. Load and Prepare Data
        graph_data, node_features_dict = await load_and_prepare_data(binance_client, telemetry)
        if graph_data is None:
            logger.error("Failed to prepare graph data. Aborting training.")
            await telemetry.send_status_update(status="error", message="Failed to prepare graph data.")
            return

        # Determine num_node_features and num_classes
        num_node_features = graph_data.x.shape[1]
        # For node classification, num_classes is typically the number of target classes.
        # Here, it's UP, DOWN, SIDEWAYS (3 classes).
        num_classes = 3 

        # Initialize GNN Model
        model = GNNModel(num_node_features, num_classes)
        optimizer = torch.optim.Adam(model.parameters(), lr=config.LEARNING_RATE)
        criterion = F.nll_loss # Negative Log Likelihood Loss

        # --- Training Loop ---
        logger.info(f"Starting GNN training for {config.EPOCHS} epochs...")
        for epoch in range(config.EPOCHS):
            if stop_event.is_set():
                logger.info("Stop event received, cancelling training.")
                await telemetry.send_status_update(status="interrupted", message="Training interrupted by stop command.")
                break

            model.train()
            optimizer.zero_grad()
            
            # Forward pass (assuming graph_data is a single PyG Data object)
            out = model(graph_data)
            
            # Placeholder for target labels (y) and masks (train_mask)
            # In a real scenario, you'd have historical labels for training
            # For now, let's create dummy labels and a dummy mask
            dummy_y = torch.randint(0, num_classes, (graph_data.num_nodes,))
            train_mask = torch.ones(graph_data.num_nodes, dtype=torch.bool) # Train on all nodes for simplicity

            loss = criterion(out[train_mask], dummy_y[train_mask])
            loss.backward()
            optimizer.step()

            training_loss.set(loss.item())
            training_epochs_completed.inc()
            logger.debug(f"Epoch {epoch+1}/{config.EPOCHS}, Loss: {loss.item():.4f}")
            await telemetry.send_status_update(
                status="loading",
                message=f"Epoch {epoch+1} completed, loss: {loss.item():.4f}",
                extra={"epoch": epoch+1, "loss": loss.item()}
            )
            await asyncio.sleep(0.1) # Small sleep to yield control

        logger.info("GNN model training completed.")
        await telemetry.send_status_update(status="loading", message="GNN model training completed.")

        # 2. Save Trained Model
        await save_model_to_minio(model, telemetry) # Pass the actual model object

    except asyncio.CancelledError:
        logger.info("GNN trainer task cancelled.")
        await telemetry.send_status_update(status="interrupted", message="GNN trainer task cancelled.")
    except Exception as e:
        logger.error(f"Fatal error in GNN trainer: {e}", exc_info=True)
        await telemetry.send_status_update(status="error", message="Fatal GNN trainer error", error_message=str(e))
    finally:
        if binance_client:
            await binance_client.close()
        logger.info("GNN trainer orchestrator finished.")
        # Final telemetry status will be sent from main.py

# Re-define save_model_to_minio here to avoid circular import if it's in trainer.py
async def save_model_to_minio(model, telemetry: TelemetryProducer):
    """Saves the trained model to Minio."""
    logger.info(f"Saving model {config.MODEL_NAME} to Minio bucket {config.MINIO_BUCKET_NAME}...")
    await telemetry.send_status_update(status="loading", message="Saving model to Minio.")

    try:
        minio_client = Minio(
            config.MINIO_ENDPOINT,
            access_key=config.MINIO_ACCESS_KEY,
            secret_key=config.MINIO_SECRET_KEY,
            secure=False # Use secure=True for HTTPS
        )

        # Ensure bucket exists
        if not minio_client.bucket_exists(config.MINIO_BUCKET_NAME):
            minio_client.make_bucket(config.MINIO_BUCKET_NAME)
            logger.info(f"Created Minio bucket: {config.MINIO_BUCKET_NAME}")

        # Save model to a temporary file first
        model_filename = f"{config.MODEL_NAME}_{int(time.time())}.pth"
        temp_filepath = f"/tmp/{model_filename}"
        torch.save(model.state_dict(), temp_filepath) # Save state_dict, not the whole model object

        # Upload the file
        minio_client.fput_object(
            config.MINIO_BUCKET_NAME,
            model_filename,
            temp_filepath,
            content_type="application/octet-stream"
        )
        logger.info(f"Model saved to Minio: {model_filename}")
        model_saved_total.inc()
        await telemetry.send_status_update(status="finished", message=f"Model {model_filename} saved to Minio.", extra={"model_filename": model_filename})
        os.remove(temp_filepath) # Clean up temp file

    except Exception as e:
        logger.error(f"Error saving model to Minio: {e}", exc_info=True)
        await telemetry.send_status_update(status="error", message="Error saving model to Minio.", error_message=str(e))
        return False
    return True