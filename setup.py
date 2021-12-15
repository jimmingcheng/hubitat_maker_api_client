from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='hubitat_maker_api_client',
    version='2.1.0',
    description='Hubitat Maker API Client',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='',
    author='Jimming Cheng',
    author_email='jimming@gmail.com',
    packages=['hubitat_maker_api_client'],
    install_requires=[
        'requests',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
