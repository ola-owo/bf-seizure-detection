import setuptools

with open("README.md", "r") as f:
    readme = f.read()

setuptools.setup(
    name="blackfynn-seizure-detection",
    version="1.0",
    author="Ola Owoputi",
    author_email="ola.owoputi@gmail.com",
    description="Automated seizure detection on Blackfynn",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/technoto/blackfynn-seizure-detection",
    packages=setuptools.find_packages(),
    classifiers=(
        "Programming Language :: Python :: 2",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ),
)
