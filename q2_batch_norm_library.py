"""
Q2. Batch Normalization Implementation USING Standard Library (PyTorch)
=======================================================================
Network Architecture:
- Input Layer: 3 neurons
- Hidden Layer 1: 3 neurons
- Hidden Layer 2: 3 neurons
- Output Layer: 2 neurons

Hyperparameters:
- Epsilon = 0.01
- Gamma (lambda) = 0.2
- Beta = 1.3
- Batch size = 3
"""

import numpy as np

# Try importing PyTorch, fall back to manual implementation if not available
try:
    import torch
    import torch.nn as nn
    PYTORCH_AVAILABLE = True
except ImportError:
    PYTORCH_AVAILABLE = False
    print("Warning: PyTorch not found. Please install it using: pip install torch")


# =====================================================================
# NEURAL NETWORK WITH BATCH NORMALIZATION USING PYTORCH
# =====================================================================

class ANNWithBatchNormPyTorch(nn.Module):
    """
    Artificial Neural Network with Batch Normalization using PyTorch
    """
    
    def __init__(self, epsilon=0.01, gamma=0.2, beta=1.3):
        super(ANNWithBatchNormPyTorch, self).__init__()
        
        # Store hyperparameters
        self.epsilon = epsilon
        self.gamma_val = gamma
        self.beta_val = beta
        
        # ─────────────────────────────────────────────────────────────────
        # Define Layers
        # ─────────────────────────────────────────────────────────────────
        
        # Layer 1: Input (3) -> Hidden1 (3)
        self.layer1 = nn.Linear(3, 3, bias=False)
        self.bn1 = nn.BatchNorm1d(3, eps=epsilon)
        
        # Layer 2: Hidden1 (3) -> Hidden2 (3)
        self.layer2 = nn.Linear(3, 3, bias=False)
        self.bn2 = nn.BatchNorm1d(3, eps=epsilon)
        
        # Layer 3: Hidden2 (3) -> Output (2)
        self.layer3 = nn.Linear(3, 2, bias=False)
        self.bn3 = nn.BatchNorm1d(2, eps=epsilon)
        
        # Activation function
        self.sigmoid = nn.Sigmoid()
        
        # Initialize weights with given values
        self._initialize_weights()
        
        # Set BatchNorm gamma and beta parameters
        self._set_batchnorm_params()
    
    def _initialize_weights(self):
        """Initialize weights with the given weight vectors"""
        
        # Wih1: Input -> Hidden1 (3x3 matrix)
        W_input_hidden1 = torch.tensor([
            [-0.2, 1.2, 3.4],
            [-4.3, 2.25, 9.1],
            [-8.9, 0.08, 1.2]
        ], dtype=torch.float32)
        self.layer1.weight = nn.Parameter(W_input_hidden1.T)
        
        # Wh1h2: Hidden1 -> Hidden2 (3x3 matrix)
        W_hidden1_hidden2 = torch.tensor([
            [-0.25, 1.12, 13.4],
            [-4.3, 2.25, 9.12],
            [-9.9, 0.08, 1.25]
        ], dtype=torch.float32)
        self.layer2.weight = nn.Parameter(W_hidden1_hidden2.T)
        
        # Wh2O: Hidden2 -> Output (3x2 matrix)
        W_hidden2_output = torch.tensor([
            [-0.25, 1.12],
            [-11.4, 4.13],
            [2.25, 9.12]
        ], dtype=torch.float32)
        self.layer3.weight = nn.Parameter(W_hidden2_output.T)
    
    def _set_batchnorm_params(self):
        """Set gamma and beta for batch normalization layers"""
        
        # For each BatchNorm layer, set gamma (weight) and beta (bias)
        # gamma = 0.2 (scale), beta = 1.3 (shift)
        
        with torch.no_grad():
            # BatchNorm1 (3 features)
            self.bn1.weight.fill_(self.gamma_val)  # gamma
            self.bn1.bias.fill_(self.beta_val)      # beta
            
            # BatchNorm2 (3 features)
            self.bn2.weight.fill_(self.gamma_val)
            self.bn2.bias.fill_(self.beta_val)
            
            # BatchNorm3 (2 features)
            self.bn3.weight.fill_(self.gamma_val)
            self.bn3.bias.fill_(self.beta_val)
    
    def forward(self, x, verbose=True):
        """
        Forward pass through the network
        
        Parameters:
        -----------
        x       : Input tensor of shape (batch_size, 3)
        verbose : Whether to print intermediate outputs
        
        Returns:
        --------
        Output tensor of shape (batch_size, 2)
        """
        if verbose:
            print("\n" + "=" * 70)
            print("FORWARD PASS WITH BATCH NORMALIZATION (PyTorch)")
            print("=" * 70)
        
        # ─────────────────────────────────────────────────────────────────
        # Layer 1: Input -> Hidden Layer 1
        # ─────────────────────────────────────────────────────────────────
        if verbose:
            print("\n[LAYER 1: Input → Hidden Layer 1]")
            print("-" * 50)
        
        z1 = self.layer1(x)
        if verbose:
            print(f"Linear output (before batch norm):\n{z1.detach().numpy()}")
        
        z1_bn = self.bn1(z1)
        if verbose:
            print(f"\nAfter Batch Normalization:\n{z1_bn.detach().numpy()}")
        
        a1 = self.sigmoid(z1_bn)
        if verbose:
            print(f"\nAfter Sigmoid Activation:\n{a1.detach().numpy()}")
        
        # ─────────────────────────────────────────────────────────────────
        # Layer 2: Hidden Layer 1 -> Hidden Layer 2
        # ─────────────────────────────────────────────────────────────────
        if verbose:
            print("\n[LAYER 2: Hidden Layer 1 → Hidden Layer 2]")
            print("-" * 50)
        
        z2 = self.layer2(a1)
        if verbose:
            print(f"Linear output (before batch norm):\n{z2.detach().numpy()}")
        
        z2_bn = self.bn2(z2)
        if verbose:
            print(f"\nAfter Batch Normalization:\n{z2_bn.detach().numpy()}")
        
        a2 = self.sigmoid(z2_bn)
        if verbose:
            print(f"\nAfter Sigmoid Activation:\n{a2.detach().numpy()}")
        
        # ─────────────────────────────────────────────────────────────────
        # Layer 3: Hidden Layer 2 -> Output Layer
        # ─────────────────────────────────────────────────────────────────
        if verbose:
            print("\n[LAYER 3: Hidden Layer 2 → Output Layer]")
            print("-" * 50)
        
        z3 = self.layer3(a2)
        if verbose:
            print(f"Linear output (before batch norm):\n{z3.detach().numpy()}")
        
        z3_bn = self.bn3(z3)
        if verbose:
            print(f"\nAfter Batch Normalization:\n{z3_bn.detach().numpy()}")
        
        output = self.sigmoid(z3_bn)
        if verbose:
            print(f"\nFinal Output (After Sigmoid):\n{output.detach().numpy()}")
        
        return output


def display_network_info(model):
    """Display network architecture and parameters"""
    print("\n" + "=" * 70)
    print("NETWORK ARCHITECTURE & PARAMETERS (PyTorch Model)")
    print("=" * 70)
    
    print("\nNetwork Structure:")
    print("   - Input Layer:    3 neurons")
    print("   - Hidden Layer 1: 3 neurons + BatchNorm1d")
    print("   - Hidden Layer 2: 3 neurons + BatchNorm1d")
    print("   - Output Layer:   2 neurons + BatchNorm1d")
    
    print("\nHyperparameters:")
    print(f"   - Epsilon: {model.epsilon}")
    print(f"   - Gamma:   {model.gamma_val}")
    print(f"   - Beta:    {model.beta_val}")
    
    print("\nWeight Matrices:")
    print(f"\nLayer 1 weights (transposed for PyTorch format):\n{model.layer1.weight.detach().numpy().T}")
    print(f"\nLayer 2 weights (transposed for PyTorch format):\n{model.layer2.weight.detach().numpy().T}")
    print(f"\nLayer 3 weights (transposed for PyTorch format):\n{model.layer3.weight.detach().numpy().T}")
    
    print("\nBatchNorm Parameters:")
    print(f"\nBN1 - gamma: {model.bn1.weight.detach().numpy()}, beta: {model.bn1.bias.detach().numpy()}")
    print(f"BN2 - gamma: {model.bn2.weight.detach().numpy()}, beta: {model.bn2.bias.detach().numpy()}")
    print(f"BN3 - gamma: {model.bn3.weight.detach().numpy()}, beta: {model.bn3.bias.detach().numpy()}")


def display_model_summary(model):
    """Display PyTorch model summary"""
    print("\n" + "=" * 70)
    print("PyTorch MODEL SUMMARY")
    print("=" * 70)
    print(model)
    
    # Count parameters
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
    
    print(f"\nTotal Parameters: {total_params}")
    print(f"Trainable Parameters: {trainable_params}")


# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":
    print("╔" + "═" * 68 + "╗")
    print("║  Q2: BATCH NORMALIZATION USING STANDARD LIBRARY (PyTorch)         ║")
    print("╚" + "═" * 68 + "╝")
    
    if not PYTORCH_AVAILABLE:
        print("\nError: Cannot proceed without PyTorch.")
        print("Please install PyTorch: pip install torch")
        exit(1)
    
    # Initialize the network
    model = ANNWithBatchNormPyTorch(epsilon=0.01, gamma=0.2, beta=1.3)
    
    # Set model to evaluation mode for consistent batch norm behavior
    model.train()  # Use training mode to see batch statistics
    
    # Display model summary
    display_model_summary(model)
    
    # Display network information
    display_network_info(model)
    
    # Create input batch (batch_size=3, input_features=3)
    # Using the given input [2.3, -1.9, 7.2] as base and creating a batch
    input_data = np.array([
        [2.3, -1.9, 7.2],   # Sample 1 (given input)
        [1.5, 0.5, 3.2],    # Sample 2
        [3.1, -0.8, 5.5]    # Sample 3
    ], dtype=np.float32)
    
    # Convert to PyTorch tensor
    input_tensor = torch.tensor(input_data)
    
    print("\n" + "=" * 70)
    print("INPUT DATA (Batch of 3 samples)")
    print("=" * 70)
    print(f"\nInput Batch Shape: {input_tensor.shape}")
    print(f"Input Batch:\n{input_tensor.numpy()}")
    
    # Perform forward pass with batch normalization
    with torch.no_grad():
        output = model(input_tensor, verbose=True)
    
    # Final Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nInput Shape:  {input_tensor.shape}")
    print(f"Output Shape: {output.shape}")
    print(f"\nFinal Network Output:\n{output.numpy()}")
    
    print("\n" + "─" * 70)
    print("PyTorch BatchNorm1d Details:")
    print("─" * 70)
    print("• nn.BatchNorm1d(num_features, eps=epsilon)")
    print("• weight parameter = gamma (scale)")
    print("• bias parameter = beta (shift)")
    print("• Formula: y = (x - E[x]) / sqrt(Var[x] + eps) * gamma + beta")
    print("─" * 70)
    
    # ─────────────────────────────────────────────────────────────────
    # Comparison Section
    # ─────────────────────────────────────────────────────────────────
    print("\n" + "=" * 70)
    print("COMPARISON: STANDARD LIBRARY vs MANUAL IMPLEMENTATION")
    print("=" * 70)
    print("""
    Advantages of using PyTorch BatchNorm:
    ---------------------------------------
    1. Optimized for GPU acceleration
    2. Handles training/evaluation modes automatically
    3. Maintains running statistics for inference
    4. Built-in gradient computation for backpropagation
    5. Numerically stable implementation
    
    Manual Implementation is useful for:
    -------------------------------------
    1. Understanding the underlying mathematics
    2. Custom modifications to the algorithm
    3. Educational purposes
    """)
