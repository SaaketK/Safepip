from setuptools import setup, Extension

# C file will be compiled into a file named 'safepip.distance_lib'
distance_module = Extension(
    'safepip.distance_lib',
    sources=['src/safepip/distance.c']
)

setup(
    ext_modules=[distance_module],
)