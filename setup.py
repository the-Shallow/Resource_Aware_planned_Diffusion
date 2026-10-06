from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

extension_modules = [
    Pybind11Extension(
        "semantic_parallel.scheduler._scheduler_native",
        [
            "semantic_parallel/scheduler/native/bindings.cpp",
            "semantic_parallel/scheduler/native/scheduler.cpp",
        ],
        cxx_std=17,
    )
]

setup(
    ext_modules=extension_modules,
    cmdclass={"build_ext": build_ext}
)