from setuptools import setup, find_packages

setup(
    name="RAG_o1",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "langchain>=0.1.0",
        "langchain-community>=0.0.10",
        "qdrant-client>=1.6.0",
        "sentence-transformers>=2.2.2",
        "python-dotenv>=1.0.0",
        "beautifulsoup4>=4.12.2",
        "markdown>=3.5.1",
        "pdfminer.six>=20221105",
        "loguru>=0.7.2",
        "pandas>=2.1.3",
        "numpy>=1.24.3",
        "torch>=2.1.1",
        "transformers>=4.35.2",
        "networkx>=3.2.1",
        "matplotlib>=3.8.2",
        "pydantic>=2.5.2",
        "typing-extensions>=4.8.0"
    ],
    author="Cline",
    description="Graph-based RAG System for Ceria Research Papers",
    python_requires=">=3.8",
)
