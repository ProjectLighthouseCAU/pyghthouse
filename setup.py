from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pyghthouse',
    version='0.3.0',
    packages=find_packages(where='.'),
    url='https://github.com/ProjectLighthouseCAU/pyghthouse',
    license='MIT',
    author='Gavin Lüdemann, Nico Penning',
    author_email='gavin.luedemann@gmail.com, nico.penning1@gmail.com',
    description='Python Lighthouse adapter',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=[
        'websocket-client >= 1.6, < 2',
        'msgpack >= 1.0, < 2',
    ],
    package_dir={"": ".", "utils": "./utils"},
    python_requires=">=3.8"
)
