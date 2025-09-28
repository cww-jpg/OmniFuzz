from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="omnifuzz",
    version="1.0.0",
    author="Yubo Song, Weiwei Chen, et al.",
    author_email="songyubo@seu.edu.cn",
    description="A Multi-Agent Reinforcement Learning Framework for Protocol-Aware Fuzzing in Power IoT Devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/OmniFuzz/OmniFuzz",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "omnifuzz-train=scripts.train_omnifuzz:main",
            "omnifuzz-fuzz=scripts.run_fuzzing:main", 
            "omnifuzz-eval=scripts.evaluate_performance:main",
        ],
    },
)