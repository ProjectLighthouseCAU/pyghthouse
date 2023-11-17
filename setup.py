from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='pyghthouse',
    version='0.2.1',
    packages=find_packages(where='.'),
    url='https://github.com/Musicted/pyghthouse',
    license='MIT',
    author='Gavin Lüdemann',
    author_email='gavin.luedemann@gmail.com',
    description='Python Lighthouse adapter',
    long_description=long_description,
    long_description_content_type="text/markdown",
    install_requires=['websocket-client~=1.2.1', 'msgpack~=1.0.2'],
    package_dir={"": ".", "utils": "./utils"},
    python_requires=">=3.8"
)
