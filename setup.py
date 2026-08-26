from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name='altastata',
    version='1.0.20260825.9',
    author='AltaStata Inc.',
    author_email='contact@altastata.com',
    description='Python SDK for the AltaStata sovereign data fabric — AI/ML pipelines, CLI, fsspec, and S3',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://www.altastata.com/',
    project_urls={
        'Homepage': 'https://www.altastata.com/',
        'Source': 'https://github.com/AltaStata/altastata-python-package',
        'Documentation': 'https://github.com/AltaStata/altastata-python-package#documentation',
        'Java / BSL runtime': 'https://github.com/AltaStata/sovereign-data-fabric',
    },
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # Bundle the unified mycloud runtime uber jar plus signed Bouncy Castle
        # jars, and include the packaged Console UI static bundle.
        'altastata': [
            'lib/altastata-services-*-uber.jar',
            'lib/bc*.jar',
            'grpc/v1/*.py',
            'lib/altastata-console-static/*',
            'lib/altastata-console-static/*/*',
        ],
        '': ['proto/**/*.proto']
    },
    license="Apache-2.0",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'fsspec>=2023.1.0',
        'grpcio>=1.80.0',
        'protobuf>=5.29.6',
    ],
    entry_points={
        'console_scripts': [
            'altastata=altastata.cli:main',
            'altastata-grpc-server=altastata.grpc_server:main',
        ],
    },
)

