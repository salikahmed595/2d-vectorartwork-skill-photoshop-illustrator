from setuptools import setup, find_namespace_packages

setup(
    name="cli-anything-illustrator",
    version="1.2.0",
    description="Agent-friendly CLI + MCP server for Adobe Illustrator on Windows (CLI-Anything harness).",
    packages=find_namespace_packages(include=["cli_anything.*"]),
    package_data={"cli_anything.illustrator": ["skills/*.md", "README.md", "tests/TEST.md"]},
    python_requires=">=3.10",
    install_requires=["click>=8.1", "pywin32>=306; sys_platform == 'win32'", "prompt_toolkit>=3.0", "mcp>=1.2"],
    extras_require={"test": ["pytest>=8", "pillow>=10"]},
    entry_points={"console_scripts": ["cli-anything-illustrator=cli_anything.illustrator.illustrator_cli:main"]},
)
