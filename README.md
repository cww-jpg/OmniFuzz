# OmniFuzz

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices**

OmniFuzz is a protocol-aware fuzzing framework for power IoT devices based on multi-agent reinforcement learning, designed to discover security vulnerabilities in protocol implementations of industrial control systems.

## 🚀 Features

- **🤖 Multi-agent reinforcement learning**: A dedicated agent per protocol field collaborates to discover vulnerabilities
- **🔌 Multi-protocol support**: Modbus TCP, EtherNet/IP, Siemens S7
- **🧬 Intelligent mutation strategies**: 8 mutation operations including field flipping, deletion, duplication, and more
- **🎯 Multi-objective reward**: Considers vulnerabilities found, path depth, diversity, etc.
- **📊 Comprehensive evaluation**: Compared against 8 baseline methods
- **📈 Real-time monitoring**: Resource usage and performance analysis
- **🔧 Modular design**: Easy to extend and maintain

## 📋 System Requirements

- Python 3.8+
- PyTorch 1.9+
- CUDA 11.0+ (optional, for GPU acceleration)

## 🛠️ Installation

### 1. Clone the repository

```bash
git clone https://github.com/your-username/omnifuzz.git
cd omnifuzz
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install OmniFuzz

```bash
pip install -e .
```

## 🚀 Quick Start

### Train models

```bash
# Train with default config
python scripts/train_omnifuzz.py

# Specify protocols and training episodes
python scripts/train_omnifuzz.py --protocols modbus_tcp ethernet_ip --episodes 500

# Train on GPU
python scripts/train_omnifuzz.py --device cuda
```

### Run fuzzing

```bash
# Fuzz with trained models
python scripts/run_fuzzing.py --models_dir models/ --duration 3600

# Specify output directory
python scripts/run_fuzzing.py --output_dir results/ --protocols modbus_tcp siemens_s7
```

### Performance evaluation

```bash
# Compare with baselines
python scripts/evaluate_performance.py --baselines AFL AFL++ DeepFuzz

# Generate detailed report
python scripts/evaluate_performance.py --output_dir evaluation_results/
```

## 📖 Example Usage

### Modbus TCP Example

```python
from src import PowerIoTEnvironment, AgentArray, ValueNetwork
import torch

# Create environment
env = PowerIoTEnvironment(protocols=['modbus_tcp'], config=config)

# Create agents
value_network = ValueNetwork(state_dim=100, action_dim=8)
agent_array = AgentArray('modbus_tcp', field_config, value_network, device)

# Run test
observations = env.reset()
for step in range(100):
    actions = agent_array.select_actions(observations['modbus_tcp'])
    next_obs, reward, done, info = env.step({'modbus_tcp': actions})
    observations = next_obs
```

### Custom mutation strategy

```python
from src import MutationEngine, MutationAction

# Create mutation engine
mutation_engine = MutationEngine(protocol_config)

# Apply mutation
mutated_message = mutation_engine.mutate_protocol_message(
    original_message,
    {'function_code': MutationAction.FIELD_FLIPPING}
)
```

## 📁 Project Structure

```
OmniFuzz/
├── README.md                 # Project description
├── requirements.txt          # Dependencies
├── setup.py                  # Installation config
├── config/                   # Configuration files
│   ├── default_config.yaml
│   ├── reward_weights.yaml
│   └── protocol_configs/
├── src/                      # Source code
│   ├── core/                 # Core components
│   ├── environment/          # Environment module
│   ├── fuzzing/              # Fuzzing
│   ├── training/             # Training
│   ├── utils/                # Utilities
│   └── evaluation/           # Evaluation
├── scripts/                  # Scripts
├── tests/                    # Tests
└── examples/                 # Examples
```

## 🔬 Supported Protocols

| Protocol | Port | Description | Status |
|------|------|------|------|
| Modbus TCP | 502 | Industrial automation protocol | ✅ Full support |
| EtherNet/IP | 44818 | Industrial Ethernet protocol | ✅ Full support |
| Siemens S7 | 102 | Siemens PLC protocol | ✅ Full support |

## 🧪 Mutation Strategies

- **Field Flipping**: Randomly flip bits in a field
- **Field Deletion**: Delete or zero out a field
- **Field Duplication**: Duplicate field content
- **Field Truncation**: Truncate message length
- **Field Padding**: Add padding data
- **Invalid Flag Injection**: Inject invalid flag values
- **Fields Reordering**: Reorder fields
- **Semantic Mutation**: Semantics-aware mutation

## 📊 Metrics

- **Time to First Attack**: Time to discover the first vulnerability
- **Effective Recognition Rate**: Ratio of successfully identified vulnerabilities
- **Code Coverage**: Coverage of execution paths
- **Vulnerability Diversity**: Number of distinct vulnerability types found

## 🏆 Baselines

OmniFuzz is compared with the following baselines:

- **Sulley**: Traditional fuzzing framework
- **AFL/AFL++**: Coverage-guided fuzzing
- **Peach**: Model-based fuzzing
- **SeqFuzzer**: Sequence-aware fuzzing
- **DeepFuzz**: Deep learning based fuzzing
- **DQNFuzzer**: DQN-based fuzzing
- **Q-Learning-Fuzzer**: Q-learning based fuzzing

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Developer setup

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Format code
black src/ tests/

# Type check
mypy src/
```

## 📄 License

This project is licensed under the MIT License. See [LICENSE](LICENSE).

## 📚 Citation

If you use OmniFuzz in your research, please cite our paper:

```bibtex
@article{song2024omnifuzz,
  title={OmniFuzz: A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices},
  author={Song, Yubo and Chen, Weiwei and others},
  journal={IEEE Transactions on Information Forensics and Security},
  year={2024}
}
```

## 📞 Contact

- **Authors**: Yubo Song, Weiwei Chen
- **Email**: songyubo@seu.edu.cn
- **Project Home**: https://github.com/your-username/omnifuzz
- **Issues**: https://github.com/your-username/omnifuzz/issues

## 🙏 Acknowledgements

Thanks to all developers and researchers who contributed to OmniFuzz.

---

**⚠️ Disclaimer**: This tool is intended for security research and authorized penetration testing only. Users must comply with applicable laws and must not use it for illegal purposes.
