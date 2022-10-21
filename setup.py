import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name = "hive-scrutineer",
    packages = ["scrutineer"],
    version = "1.0.0",
    license="MIT",
    description = "Performance and quality analytics on Hive Posts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = "Rodney Maniego Jr.",
    author_email = "rodney.maniegojr@gmail.com",
    url = "https://github.com/rmaniego/scrutineer",
    download_url = "https://github.com/rmaniego/scrutineer/archive/v1.0.tar.gz",
    keywords = ["hive", "blockchain", "seo", "quality", "analytics"],
    install_requires=["hive-nektar"],
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers", 
        "Topic :: Software Development :: Build Tools",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3"
    ],
    python_requires=">=3.9"
)