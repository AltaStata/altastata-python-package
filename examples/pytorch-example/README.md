# PyTorch Dataset Example

Examples for using the `altastata` package with `AltaStataPyTorchDataset` - a dataset class that integrates PyTorch workflows with encrypted AltaStata storage.

## Package Installation

Install the `altastata` package:

```bash
pip install altastata torch torchvision
```

### Dependencies

The package requires the following dependencies:
- torch
- torchvision
- numpy
- pandas
- Pillow (Python Imaging Library)

## Running Examples

After ensuring the `altastata` package is installed, you can run the examples:

```bash
cd examples/pytorch-example
python generate_sample_files.py
python test_dataset.py
python training_example.py
python inference_example.py
```

## Features

### File Content Cache
The dataset includes an intelligent file content cache that:
- Automatically caches files up to 16MB in size
- Maintains a total cache size limit of 1GB
- Removes files from cache when they are modified
- Provides detailed logging of cache operations
- Improves performance for frequently accessed files

### Multi-Process Support
The dataset is designed to work efficiently with PyTorch's DataLoader:
- Supports multiple worker processes
- Properly handles file access across processes
- Includes process-specific logging
- Maintains cache consistency across processes

## Example Descriptions

### Basic Dataset Usage
The examples demonstrate how to use the dataset with various file types:

```python
# Import the required classes from the altastata package
from altastata import AltaStataFunctions, AltaStataPyTorchDataset
from altastata.altastata_pytorch_dataset import register_altastata_functions_for_pytorch
from torch.utils.data import DataLoader
import torchvision.transforms as transforms
import torch

# Initialize AltaStata and register for PyTorch
functions = AltaStataFunctions.from_account_dir(
    "~/.altastata/accounts/amazon.rsa.bob123",
    password="your_password",
)
account_id = "my_account"
register_altastata_functions_for_pytorch(functions, account_id)

# Create dataset with transforms
transform = transforms.Compose([
    transforms.PILToTensor(),
    transforms.ConvertImageDtype(torch.float32),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

# Create dataset
dataset = AltaStataPyTorchDataset(
    account_id=account_id,
    root_dir="pytorch_test/data/images",
    file_pattern="*.jpg",  # or *.npy, *.csv
    transform=transform
)

# Use with DataLoader
dataloader = DataLoader(
    dataset,
    batch_size=32,
    shuffle=True
)

# Use in training loop
for data, labels in dataloader:
    # data is a tensor of shape [batch_size, channels, height, width] for images
    # labels are automatically generated based on filenames (1 for 'circle', 0 for others)
    pass
```

> **Note on Multi-Worker DataLoaders:** When using `DataLoader(..., num_workers > 0)` with `spawn` multiprocessing (default on macOS and Windows), ensure `register_altastata_functions_for_pytorch` is invoked in the worker initialization or main guard so worker processes can access the account registry.

### Training Example
The package includes a training example that demonstrates:
- Loading and preprocessing images
- Training a CNN model
- Model validation and saving
- Binary classification (circles vs rectangles)
- Data augmentation during training
- Early stopping and model checkpointing
- Efficient multi-process data loading

### Inference Example
The inference example shows how to:
- Load a trained model
- Preprocess new images
- Make predictions
- Display results with confidence scores
- Visualize predictions
- Use the file content cache for faster inference

## Project Structure
```
examples/pytorch-example/     # Examples using the altastata package
    test_dataset.py           # Basic dataset tests
    training_example.py       # CNN training example
    inference_example.py      # Model inference example
    generate_sample_files.py  # Creates sample data
    data/                     # Directory for sample data
        images/               # Sample images
        csv/                  # CSV files
        numpy/                # NumPy arrays
        models/              # Saved model checkpoints
    README.md                 # This documentation file

altastata/                    # Main package
    __init__.py               # Exports classes including AltaStataPyTorchDataset
    altastata_functions.py    # Core functionality
    altastata_pytorch_dataset.py # PyTorch dataset implementation
```

## License

Apache License, Version 2.0 — see the repository [LICENSE](../../LICENSE). 