#!/usr/bin/env python3

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="prompt-manager",
    version="0.0.16",
    author="Prompt Manager Team",
    author_email="team@promptmanager.dev",
    description="AI Prompt Management and Task-Master Integration System",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/promptManager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: General",
        "Topic :: Utilities",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "prompt-manager=prompt_manager.cli:main",
            "pm=prompt_manager.cli:main",
            "pmcli=prompt_manager.tm_cli:main",
            "prompt-api=prompt_manager.api:main",
            "project-registry=prompt_manager.registry_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "prompt_manager": [
            "templates/*.json",
            "assets/*",
        ],
    },
    extras_require={
        "dev": [
            "pytest>=6.0",
            "black>=21.0",
            "flake8>=3.8",
            "mypy>=0.800",
        ],
        "browser": [
            "selenium>=4.0",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-username/promptManager/issues",
        "Source": "https://github.com/your-username/promptManager",
        "Documentation": "https://github.com/your-username/promptManager/tree/main/docs",
    },
)