"""
Q1. Batch Normalization Implementation WITHOUT using Standard Library
=====================================================================
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

# =====================================================================
# BATCH NORMALIZATION FROM SCRATCH
# =====================================================================

def batch_normalize(x, gamma, beta, epsilon):
    """
    Applies batch normalization to the input.
    
    Steps:
    1. Calculate mean of the batch
    2. Calculate variance of the batch
    3. Normalize: (x - mean) / sqrt(variance + epsilon)
    4. Scale and shift: gamma * normalized + beta
    
    Parameters:
    -----------
    x       : Input values (batch of activations)
    gamma   : Scale parameter (lambda in the question)
    beta    : Shift parameter
    epsilon : Small constant for numerical stability
    
    Returns:
    --------
    Normalized, scaled, and shifted output
    """
    # Step 1: Calculate the mean of the batch
    batch_mean = np.mean(x, axis=0)
    print(f"    Batch Mean: {batch_mean}")
    
    # Step 2: Calculate the variance of the batch
    batch_variance = np.var(x, axis=0)
    print(f"    Batch Variance: {batch_variance}")
    
    # Step 3: Normalize the input
    x_normalized = (x - batch_mean) / np.sqrt(batch_variance + epsilon)
    print(f"    Normalized Values:\n{x_normalized}")
    
    # Step 4: Scale and shift using gamma and beta
    output = gamma * x_normalized + beta
    print(f"    After Scale (gamma={gamma}) and Shift (beta={beta}):\n{output}")
    
    return output, batch_mean, batch_variance, x_normalized


def sigmoid(x):
    """Sigmoid activation function"""
    return 1 / (1 + np.exp(-np.clip(x, -500, 500)))


def relu(x):
    """ReLU activation function"""
    return np.maximum(0, x)


class ANNWithBatchNorm:
    """
    Artificial Neural Network with Batch Normalization (from scratch)
    """
    
    def __init__(self, epsilon=0.01, gamma=0.2, beta=1.3):
        """
        Initialize the network with given hyperparameters and weights.
        """
        self.epsilon = epsilon
        self.gamma = gamma
        self.beta = beta
        
        # Weight matrices (reshaped from given vectors)
        # Wih1: Input (3) -> Hidden1 (3) = 3x3 = 9 weights
        self.W_input_hidden1 = np.array([
            [-0.2, 1.2, 3.4],
            [-4.3, 2.25, 9.1],
            [-8.9, 0.08, 1.2]
        ])
        
        # Wh1h2: Hidden1 (3) -> Hidden2 (3) = 3x3 = 9 weights
        self.W_hidden1_hidden2 = np.array([
            [-0.25, 1.12, 13.4],
            [-4.3, 2.25, 9.12],
            [-9.9, 0.08, 1.25]
        ])
        
        # Wh2O: Hidden2 (3) -> Output (2) = 3x2 = 6 weights
        self.W_hidden2_output = np.array([
            [-0.25, 1.12],
            [-11.4, 4.13],
            [2.25, 9.12]
        ])
        
    def forward_pass(self, X):
        """
        Forward pass through the network with batch normalization.
        
        Parameters:
        -----------
        X : Input batch of shape (batch_size, input_features)
        
        Returns:
        --------
        Final output after passing through all layers
        """
        print("\n" + "=" * 70)
        print("FORWARD PASS WITH BATCH NORMALIZATION")
        print("=" * 70)
        
        # ─────────────────────────────────────────────────────────────────
        # LAYER 1: Input -> Hidden Layer 1
        # ─────────────────────────────────────────────────────────────────
        print("\n[LAYER 1: Input → Hidden Layer 1]")
        print("-" * 50)
        
        # Linear transformation: z1 = X @ W
        z1 = np.dot(X, self.W_input_hidden1)
        print(f"Linear output (before batch norm):\n{z1}")
        
        # Apply Batch Normalization
        print("\nApplying Batch Normalization:")
        z1_bn, mean1, var1, z1_norm = batch_normalize(z1, self.gamma, self.beta, self.epsilon)
        
        # Apply activation function
        a1 = sigmoid(z1_bn)
        print(f"\nAfter Sigmoid Activation:\n{a1}")
        
        # ─────────────────────────────────────────────────────────────────
        # LAYER 2: Hidden Layer 1 -> Hidden Layer 2
        # ─────────────────────────────────────────────────────────────────
        print("\n[LAYER 2: Hidden Layer 1 → Hidden Layer 2]")
        print("-" * 50)
        
        # Linear transformation
        z2 = np.dot(a1, self.W_hidden1_hidden2)
        print(f"Linear output (before batch norm):\n{z2}")
        
        # Apply Batch Normalization
        print("\nApplying Batch Normalization:")
        z2_bn, mean2, var2, z2_norm = batch_normalize(z2, self.gamma, self.beta, self.epsilon)
        
        # Apply activation function
        a2 = sigmoid(z2_bn)
        print(f"\nAfter Sigmoid Activation:\n{a2}")
        
        # ─────────────────────────────────────────────────────────────────
        # LAYER 3: Hidden Layer 2 -> Output Layer
        # ─────────────────────────────────────────────────────────────────
        print("\n[LAYER 3: Hidden Layer 2 → Output Layer]")
        print("-" * 50)
        
        # Linear transformation
        z3 = np.dot(a2, self.W_hidden2_output)
        print(f"Linear output (before batch norm):\n{z3}")
        
        # Apply Batch Normalization
        print("\nApplying Batch Normalization:")
        z3_bn, mean3, var3, z3_norm = batch_normalize(z3, self.gamma, self.beta, self.epsilon)
        
        # Apply activation function (output layer)
        output = sigmoid(z3_bn)
        print(f"\nFinal Output (After Sigmoid):\n{output}")
        
        return output
    
    def display_network_info(self):
        """Display network architecture and parameters"""
        print("\n" + "=" * 70)
        print("NETWORK ARCHITECTURE & PARAMETERS")
        print("=" * 70)
        
        print("\nNetwork Structure:")
        print("   - Input Layer:    3 neurons")
        print("   - Hidden Layer 1: 3 neurons")
        print("   - Hidden Layer 2: 3 neurons")
        print("   - Output Layer:   2 neurons")
        
        print("\nHyperparameters:")
        print(f"   - Epsilon: {self.epsilon}")
        print(f"   - Gamma:   {self.gamma}")
        print(f"   - Beta:    {self.beta}")
        
        print("\nWeight Matrices:")
        print(f"\nW_input_hidden1 (3x3):\n{self.W_input_hidden1}")
        print(f"\nW_hidden1_hidden2 (3x3):\n{self.W_hidden1_hidden2}")
        print(f"\nW_hidden2_output (3x2):\n{self.W_hidden2_output}")


# =====================================================================
# MAIN EXECUTION
# =====================================================================

if __name__ == "__main__":
    print("╔" + "═" * 68 + "╗")
    print("║  Q1: BATCH NORMALIZATION FROM SCRATCH (WITHOUT STANDARD LIBRARY)  ║")
    print("╚" + "═" * 68 + "╝")
    
    # Initialize the network
    ann = ANNWithBatchNorm(epsilon=0.01, gamma=0.2, beta=1.3)
    
    # Display network information
    ann.display_network_info()
    
    # Create input batch (batch_size=3, input_features=3)
    # Using the given input [2.3, -1.9, 7.2] as base and creating a batch
    input_data = np.array([
        [2.3, -1.9, 7.2],   # Sample 1 (given input)
        [1.5, 0.5, 3.2],    # Sample 2
        [3.1, -0.8, 5.5]    # Sample 3
    ])
    
    print("\n" + "=" * 70)
    print("INPUT DATA (Batch of 3 samples)")
    print("=" * 70)
    print(f"\nInput Batch Shape: {input_data.shape}")
    print(f"Input Batch:\n{input_data}")
    
    # Perform forward pass with batch normalization
    output = ann.forward_pass(input_data)
    
    # Final Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"\nInput Shape:  {input_data.shape}")
    print(f"Output Shape: {output.shape}")
    print(f"\nFinal Network Output:\n{output}")
    
    print("\n" + "─" * 70)
    print("Batch Normalization Formula Used:")
    print("─" * 70)
    print("1. μ = (1/m) × Σ(xi)           [Batch Mean]")
    print("2. σ² = (1/m) × Σ(xi - μ)²     [Batch Variance]")
    print("3. x̂ = (x - μ) / √(σ² + ε)     [Normalize]")
    print("4. y = γ × x̂ + β               [Scale and Shift]")
    print("─" * 70)
