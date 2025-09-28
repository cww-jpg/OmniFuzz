# OmniFuzz

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Code Style](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices**

OmniFuzz是一个基于多智能体强化学习的电力物联网设备协议感知模糊测试框架，专门用于发现工业控制系统中协议实现的安全漏洞。

## 🚀 特性

- **🤖 多智能体强化学习**: 每个协议字段都有专用的智能体，协同工作发现漏洞
- **🔌 多协议支持**: 支持Modbus TCP、EtherNet/IP、Siemens S7等主流工业协议
- **🧬 智能变异策略**: 8种不同的变异操作，包括字段翻转、删除、复制等
- **🎯 多目标奖励函数**: 综合考虑漏洞发现数量、路径深度、多样性等因素
- **📊 完整评估体系**: 与8种基线方法进行性能比较
- **📈 实时监控**: 资源使用和性能分析
- **🔧 模块化设计**: 易于扩展和维护

## 📋 系统要求

- Python 3.8+
- PyTorch 1.9+
- CUDA 11.0+ (可选，用于GPU加速)

## 🛠️ 安装

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/omnifuzz.git
cd omnifuzz
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 安装OmniFuzz

```bash
pip install -e .
```

## 🚀 快速开始

### 训练模型

```bash
# 使用默认配置训练
python scripts/train_omnifuzz.py

# 指定协议和训练周期
python scripts/train_omnifuzz.py --protocols modbus_tcp ethernet_ip --episodes 500

# 使用GPU训练
python scripts/train_omnifuzz.py --device cuda
```

### 运行模糊测试

```bash
# 使用训练好的模型进行模糊测试
python scripts/run_fuzzing.py --models_dir models/ --duration 3600

# 指定输出目录
python scripts/run_fuzzing.py --output_dir results/ --protocols modbus_tcp siemens_s7
```

### 性能评估

```bash
# 与基线方法比较
python scripts/evaluate_performance.py --baselines AFL AFL++ DeepFuzz

# 生成详细报告
python scripts/evaluate_performance.py --output_dir evaluation_results/
```

## 📖 使用示例

### Modbus TCP 示例

```python
from src import PowerIoTEnvironment, AgentArray, ValueNetwork
import torch

# 创建环境
env = PowerIoTEnvironment(protocols=['modbus_tcp'], config=config)

# 创建智能体
value_network = ValueNetwork(state_dim=100, action_dim=8)
agent_array = AgentArray('modbus_tcp', field_config, value_network, device)

# 运行测试
observations = env.reset()
for step in range(100):
    actions = agent_array.select_actions(observations['modbus_tcp'])
    next_obs, reward, done, info = env.step({'modbus_tcp': actions})
    observations = next_obs
```

### 自定义变异策略

```python
from src import MutationEngine, MutationAction

# 创建变异引擎
mutation_engine = MutationEngine(protocol_config)

# 应用变异
mutated_message = mutation_engine.mutate_protocol_message(
    original_message, 
    {'function_code': MutationAction.FIELD_FLIPPING}
)
```

## 📁 项目结构

```
OmniFuzz/
├── README.md                 # 项目说明
├── requirements.txt          # 依赖包列表
├── setup.py                 # 安装配置
├── config/                  # 配置文件
│   ├── default_config.yaml
│   ├── reward_weights.yaml
│   └── protocol_configs/
├── src/                     # 源代码
│   ├── core/               # 核心组件
│   ├── environment/        # 环境模块
│   ├── fuzzing/           # 模糊测试
│   ├── training/           # 训练模块
│   ├── utils/              # 工具模块
│   └── evaluation/         # 评估模块
├── scripts/                # 脚本文件
├── tests/                  # 测试文件
└── examples/               # 示例代码
```

## 🔬 支持的协议

| 协议 | 端口 | 描述 | 状态 |
|------|------|------|------|
| Modbus TCP | 502 | 工业自动化协议 | ✅ 完全支持 |
| EtherNet/IP | 44818 | 工业以太网协议 | ✅ 完全支持 |
| Siemens S7 | 102 | 西门子PLC协议 | ✅ 完全支持 |

## 🧪 变异策略

- **字段翻转** (Field Flipping): 随机翻转字段中的位
- **字段删除** (Field Deletion): 删除或置零字段
- **字段复制** (Field Duplication): 复制字段内容
- **字段截断** (Field Truncation): 截断消息长度
- **字段填充** (Field Padding): 添加填充数据
- **无效标志注入** (Invalid Flag Injection): 注入无效标志值
- **字段重排序** (Fields Reordering): 重新排列字段顺序
- **语义变异** (Semantic Mutation): 基于语义的智能变异

## 📊 性能指标

- **首次攻击时间** (Time to First Attack): 发现第一个漏洞的时间
- **有效识别率** (Effective Recognition Rate): 成功识别的漏洞比例
- **代码覆盖率** (Code Coverage): 执行路径的覆盖率
- **漏洞多样性** (Vulnerability Diversity): 发现的不同类型漏洞数量

## 🏆 基线比较

OmniFuzz与以下基线方法进行了比较：

- **Sulley**: 传统模糊测试框架
- **AFL/AFL++**: 基于覆盖率的模糊测试
- **Peach**: 基于模型的模糊测试
- **SeqFuzzer**: 序列感知模糊测试
- **DeepFuzz**: 基于深度学习的模糊测试
- **DQNFuzzer**: 基于DQN的模糊测试
- **Q-Learning-Fuzzer**: 基于Q学习的模糊测试

## 🤝 贡献

我们欢迎各种形式的贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详细信息。

### 开发环境设置

```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 运行测试
pytest tests/

# 代码格式化
black src/ tests/

# 类型检查
mypy src/
```

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📚 引用

如果您在研究中使用了OmniFuzz，请引用我们的论文：

```bibtex
@article{song2024omnifuzz,
  title={OmniFuzz: A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices},
  author={Song, Yubo and Chen, Weiwei and others},
  journal={IEEE Transactions on Information Forensics and Security},
  year={2024}
}
```

## 📞 联系方式

- **作者**: Yubo Song, Weiwei Chen
- **邮箱**: songyubo@seu.edu.cn
- **项目主页**: https://github.com/your-username/omnifuzz
- **问题反馈**: https://github.com/your-username/omnifuzz/issues

## 🙏 致谢

感谢所有为OmniFuzz项目做出贡献的开发者和研究人员。

---

**⚠️ 免责声明**: 本工具仅用于安全研究和授权的渗透测试。使用者需要确保遵守相关法律法规，不得用于非法用途。
