from setuptools import setup

metadata = {}
with open("adaptive/_metadata.py") as fp:
    exec(fp.read(), metadata)

setup(name='datawire-adaptive',
      version=metadata["__version__"],
      description=metadata["__summary__"],
      author=metadata["__author__"],
      author_email=metadata["__email__"],
      url=metadata["__uri__"],
      license=metadata["__license__"],
      packages=['adaptive'],
      install_requires=["docopt==0.6.2",
                        "parsimonious==0.6.2"],
      entry_points={"console_scripts": ["adaptive = adaptive.codegen:call_main"]}
      )
