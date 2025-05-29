#!/usr/bin/env python3
"""
Setup script for the subdomain scanner package.
"""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="subdomain-scanner",
    version="1.0.0",
    author="Subdomain Scanner Contributors",
    author_email="",
    description="High-performance async subdomain scanner with intelligent caching",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/subdomain-scanner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Security",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "subdomain-scanner=cli:main",
        ],
    },
    keywords="subdomain scanner security async http",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/subdomain-scanner/issues",
        "Source": "https://github.com/yourusername/subdomain-scanner",
    },
)
