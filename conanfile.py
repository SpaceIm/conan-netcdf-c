import os

from conans import ConanFile, CMake, tools
from conans.errors import ConanInvalidConfiguration

class NetcdfConan(ConanFile):
    name = "netcdf-c"
    description = "The Unidata network Common Data Form (netCDF) is an interface " \
                  "for scientific data access and a freely-distributed software " \
                  "library that provides an implementation of the interface."
    license = "BSD-3-Clause"
    topics = ("conan", "netcdf-c", "netcdf")
    homepage = "https://github.com/Unidata/netcdf-c"
    url = "https://github.com/conan-io/conan-center-index"
    exports_sources = ["CMakeLists.txt", "patches/**"]
    generators = "cmake", "cmake_find_package"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_utilities": [True, False],
        "netcdf4": [True, False],
        "hdf4": [True, False],
        "hdf5": [True, False],
        "dap": [True, False],
        "parallel": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_utilities": True,
        "netcdf4": True,
        "hdf4": False,
        "hdf5": True,
        "dap": True,
        "parallel": False,
    }

    _cmake = None

    @property
    def _source_subfolder(self):
        return "source_subfolder"

    @property
    def _build_subfolder(self):
        return "build_subfolder"

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            del self.options.fPIC
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx

        if self.options.netcdf4 and not self.options.hdf5:
            raise ConanInvalidConfiguration("netcdf4 requires hdf5")
        if not self.options.netcdf4:
            if self.options.hdf4:
                raise ConanInvalidConfiguration("netcdf4 is required for hdf4 features")
            if self.options.parallel:
                raise ConanInvalidConfiguration("netcdf4 is required for parallel IO")
        self._strict_options_requirements()

    def _strict_options_requirements(self):
        if self.options.hdf5:
            self.options["hdf5"].with_zlib = True
            self.options["hdf5"].hl = True
            if self.options.parallel:
                raise ConanInvalidConfiguration("parallel option requires openmpi which is not yet available in CCI")
                self.options["hdf5"].parallel = True # TODO: option not yet available in hdf5 recipe, requires openmpi in CCI

    def requirements(self):
        if self.options.hdf4:
            self.requires("hdf4/4.2.15")
        if self.options.hdf5:
            self.requires("hdf5/1.12.0")
        if self.options.dap:
            self.requires("libcurl/7.72.0")
        if self.options.parallel:
            self.requires("openmpi/4.0.3")

    def _validate_dependency_graph(self):
        if self.options.hdf5:
            if not (self.options["hdf5"].with_zlib and self.options["hdf5"].hl):
                raise ConanInvalidConfiguration("netcdf-c requires hdf5 with zlib and hl")
            if self.options.parallel and not self.options["hdf5"].parallel:
                raise ConanInvalidConfiguration("netcdf-c parallel requires hdf5 parallel")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        self._validate_dependency_graph()
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        cmake = CMake(self)
        if self.settings.compiler == "Visual Studio":
            cmake.definitions["NC_USE_STATIC_CRT"] = str(self.settings.compiler.runtime).startswith("MT")
        cmake.definitions["ENABLE_V2_API"] = True
        cmake.definitions["BUILD_UTILITIES"] = self.options.build_utilities
        cmake.definitions["ENABLE_MMAP"] = True
        cmake.definitions["ENABLE_EXAMPLES"] = False
        cmake.definitions["ENABLE_HDF4"] = self.options.hdf4
        if self.options.hdf4:
            cmake.definitions["ENABLE_HDF4_FILE_TESTS"] = False
        cmake.definitions["ENABLE_NETCDF_4"] = self.options.netcdf4
        cmake.definitions["ENABLE_LOGGING"] = False
        cmake.definitions["ENABLE_SET_LOG_LEVEL_FUNC"] = True
        cmake.definitions["ENABLE_STRICT_NULL_BYTE_HEADER_PADDING"] = False
        cmake.definitions["ENABLE_RPC"] = False
        cmake.definitions["USE_HDF5"] = self.options.hdf5
        if self.options.hdf5:
            cmake.definitions["NC_ENABLE_HDF_16_API"] = True
        cmake.definitions["ENABLE_DAP"] = self.options.dap
        cmake.definitions["ENABLE_BYTERANGE"] = False
        cmake.definitions["ENABLE_DAP_LONG_TESTS"] = False
        cmake.definitions["ENABLE_DAP_REMOTE_TESTS"] = False
        cmake.definitions["ENABLE_EXTRA_TESTS"] = False
        if self.settings.compiler == "Visual Studio":
            cmake.definitions["ENABLE_XGETOPT"] = True
        if self.settings.os != "Windows":
            cmake.definitions["ENABLE_STDIO"] = False
            cmake.definitions["ENABLE_FFIO"] = False
        cmake.definitions["ENABLE_TESTS"] = False
        cmake.definitions["ENABLE_EXTREME_NUMBERS"] = False
        cmake.definitions["ENABLE_METADATA_PERF_TESTS"] = False
        cmake.definitions["ENABLE_FSYNC"] = False # Option?
        cmake.definitions["ENABLE_JNA"] = False
        cmake.definitions["ENABLE_LARGE_FILE_SUPPORT"] = True # Option?
        cmake.definitions["ENABLE_EXAMPLE_TESTS"] = False
        cmake.definitions["ENABLE_PARALLEL4"] = self.options.parallel
        cmake.definitions["ENABLE_PNETCDF"] = False
        cmake.definitions["ENABLE_ERANGE_FILL"] = False
        cmake.definitions["ENABLE_PARALLEL_TESTS"] = False
        cmake.definitions["ENABLE_FILTER_TESTING"] = False
        cmake.definitions["ENABLE_CLIENTSIDE_FILTERS"] = False
        cmake.definitions["ENABLE_DOXYGEN"] = False
        cmake.definitions["ENABLE_DISKLESS"] = True
        if self.settings.compiler == "Visual Studio":
            cmake.definitions["NC_MSVC_STACK_SIZE"] = 40000000 # Option?
        cmake.definitions["ENABLE_CDF5"] = True
        cmake.definitions["ENABLE_BASH_SCRIPT_TESTING"] = False
        cmake.configure(build_folder=self._build_subfolder)
        self._cmake = cmake
        return self._cmake

    def package(self):
        self.copy("COPYRIGHT", dst="licenses", src=self._source_subfolder)
        cmake = self._configure_cmake()
        cmake.install()
        os.remove(os.path.join(self.package_folder, "bin", "nc-config"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "cmake"))
        tools.rmdir(os.path.join(self.package_folder, "lib", "pkgconfig"))
        os.remove(os.path.join(self.package_folder, "lib", "libnetcdf.settings"))
        tools.rmdir(os.path.join(self.package_folder, "share"))

    def package_info(self):
        self.cpp_info.names["cmake_find_package"] = "netCDF"
        self.cpp_info.names["cmake_find_package_multi"] = "netCDF"
        self.cpp_info.names["pkg_config"] = "netcdf"
        self.cpp_info.components["netcdf"].names["cmake_find_package"] = "netcdf"
        self.cpp_info.components["netcdf"].names["cmake_find_package_multi"] = "netcdf"
        self.cpp_info.components["netcdf"].names["pkg_config"] = "netcdf"
        self.cpp_info.components["netcdf"].libs = tools.collect_libs(self)
        if self.options.hdf4:
            self.cpp_info.components["netcdf"].requires.append("hdf4::hdf4")
        if self.options.hdf5:
            self.cpp_info.components["netcdf"].requires.append("hdf5::hdf5") # TODO: when components available in hdf5 recipe => requires.extend([hdf5::hl, hdf5::c])
        if self.options.dap:
            self.cpp_info.components["netcdf"].requires.append("libcurl::libcurl")
        if self.options.parallel:
            self.cpp_info.components["netcdf"].requires.append("openmpi::openmpi")
        if self.settings.os == "Linux":
            self.cpp_info.components["netcdf"].system_libs = ["m"]
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.components["netcdf"].defines.append("DLL_NETCDF")
