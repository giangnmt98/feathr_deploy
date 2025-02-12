import sys
import os
from setuptools import setup, find_packages
from pathlib import Path


# Use the README.md from /docs
root_path = Path(__file__).resolve().parent.parent
readme_path = root_path / "docs/README.md"
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf8")
else:
    # In some build environments (specifically in conda), we may not have the README file
    # readily available. In these cases, just set long_description to the URL of README.md.
    long_description = "See https://github.com/feathr-ai/feathr/blob/main/docs/README.md"

try:
    exec(open("feathr/version.py").read())
except IOError:
    print("Failed to load Feathr version file for packaging.", file=sys.stderr)
    # Temp workaround for conda build. For long term fix, Jay will need to update manifest.in file.
    VERSION = "1.0.0"

VERSION = __version__  # noqa
os.environ["FEATHR_VERSION"] = VERSION

extras_require = dict(
    dev=[
        "black>=22.1.0",  # formatter
        "isort",  # sort import statements
        "pytest>=7",
        "pytest-cov",
        "pytest-xdist",
        "pytest-mock>=3.8.1",
    ],
    notebook=[
        "azure-cli==2.37.0",
        "jupyter>=1.0.0",
        "matplotlib>=3.6.1",
        "papermill>=2.1.2,<3",  # to test run notebooks
        "scrapbook>=0.5.0,<1.0.0",  # to scrap notebook outputs
        "scikit-learn",  # for notebook examples
        "plotly",  # for plotting
    ],
)
extras_require["all"] = list(set(sum([*extras_require.values()], [])))

setup(
    name="feathr",
    version=VERSION,
    long_description=long_description,
    long_description_content_type="text/markdown",
    author_email="feathr-technical-discuss@lists.lfaidata.foundation",
    description="An Enterprise-Grade, High Performance Feature Store",
    url="https://github.com/data-science-general-1/feathr",
    project_urls={
        "Bug Tracker": "https://github.com/feathr-ai/feathr/issues",
    },
    packages=find_packages(),
    include_package_data=True,
    # consider
    install_requires=[
        "click<=8.1.3",
        "py4j==0.10.9.5",
        "loguru<=0.6.0",
        "pandas",
        "redis<=4.4.0",
        "redis-py-cluster==2.1.3",
        "pymongo==4.10.1",
        "requests<=2.28.1",
        "tqdm<=4.64.1",
        "pyapacheatlas<=0.14.0",
        "pyhocon<=0.3.59",
        "pyyaml<=6.0",
        "Jinja2<=3.1.2",
        "pyarrow<=11.0.0",
        "pyspark==3.4.1",  # TODO upgrade the version once pyspark publishes new release to resolve `AttributeError: module 'numpy' has no attribute 'bool'`
        "python-snappy<=0.6.1",
        "graphlib_backport<=1.0.3",
        "protobuf<=3.19.4,>=3.0.0",
        "confluent-kafka",
        # Synapse's aiohttp package is old and does not work with Feathr. We pin to a newer version here.
        "aiohttp==3.8.3",
        "msrest<=0.6.21",
        "typing_extensions>=4.2.0",
        "kafka-python",
        "ipython",  # for chat in notebook
        "numpy==1.26.4",
        "psutil"
    ],
    tests_require=[  # TODO: This has been depricated
        "pytest",
    ],
    extras_require=extras_require,
    entry_points={"console_scripts": ["feathr=feathrcli.cli:cli"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
)
