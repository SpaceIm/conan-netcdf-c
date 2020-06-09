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
    generators = "cmake"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "build_utilities": [True, False],
        "netcdf_4": [True, False],
        "hdf4": [True, False],
        "hdf5": [True, False],
        "dap": [True, False],
        "parallel": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "build_utilities": True,
        "netcdf_4": True,
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
        del self.settings.compiler.cppstd
        del self.settings.compiler.libcxx
        if not self.options.netcdf_4:
            del self.options.hdf4
            del self.options.hdf5
        if not (self.options.netcdf_4 and self.options.hdf5):
            del self.options.parallel
        if self.options.get_safe("hdf5", False):
            self.options["hdf5"].with_zlib = True
            self.options["hdf5"].hl = True
        if self.options.get_safe("parallel", False):
            raise ConanInvalidConfiguration("parallel option requires openmpi which is not yet available in CCI")
            self.options["hdf5"].parallel = True # TODO: option not yet available in hdf5 recipe, requires openmpi in CCI

    def requirements(self):
        if self.options.get_safe("hdf4", False):
            self.requires("hdf4/4.2.15")
        if self.options.get_safe("hdf5", False):
            self.requires("hdf5/1.12.0")
        if self.options.dap:
            self.requires("libcurl/7.70.0")
        if self.options.get_safe("parallel", False):
            self.requires("openmpi/4.0.3")

    def source(self):
        tools.get(**self.conan_data["sources"][self.version])
        os.rename(self.name + "-" + self.version, self._source_subfolder)

    def build(self):
        for patch in self.conan_data.get("patches", {}).get(self.version, []):
            tools.patch(**patch)
        cmake = self._configure_cmake()
        cmake.build()

    def _configure_cmake(self):
        if self._cmake:
            return self._cmake
        self._cmake = CMake(self)
        if self.settings.compiler == "Visual Studio":
            self._cmake.definitions["NC_USE_STATIC_CRT"] = str(self.settings.compiler.runtime).startswith("MT")
        self._cmake.definitions["ENABLE_V2_API"] = True
        self._cmake.definitions["BUILD_UTILITIES"] = self.options.build_utilities
        self._cmake.definitions["ENABLE_MMAP"] = True
        self._cmake.definitions["ENABLE_EXAMPLES"] = False
        self._cmake.definitions["ENABLE_HDF4"] = self.options.get_safe("hdf4", False)
        if self.options.get_safe("hdf4", False):
            self._cmake.definitions["ENABLE_HDF4_FILE_TESTS"] = False
        self._cmake.definitions["ENABLE_NETCDF_4"] = self.options.netcdf_4
        self._cmake.definitions["ENABLE_LOGGING"] = False
        self._cmake.definitions["ENABLE_SET_LOG_LEVEL_FUNC"] = True
        self._cmake.definitions["ENABLE_STRICT_NULL_BYTE_HEADER_PADDING"] = False
        self._cmake.definitions["ENABLE_RPC"] = False
        self._cmake.definitions["USE_HDF5"] = self.options.get_safe("hdf5", False)
        if self.options.get_safe("hdf5", False):
            self._cmake.definitions["NC_ENABLE_HDF_16_API"] = True
        self._cmake.definitions["ENABLE_DAP"] = self.options.dap
        self._cmake.definitions["ENABLE_BYTERANGE"] = False
        self._cmake.definitions["ENABLE_DAP_LONG_TESTS"] = False
        self._cmake.definitions["ENABLE_DAP_REMOTE_TESTS"] = False
        self._cmake.definitions["ENABLE_EXTRA_TESTS"] = False
        if self.settings.compiler == "Visual Studio":
            self._cmake.definitions["ENABLE_XGETOPT"] = True
        if self.settings.os != "Windows":
            self._cmake.definitions["ENABLE_STDIO"] = False
            self._cmake.definitions["ENABLE_FFIO"] = False
        self._cmake.definitions["ENABLE_TESTS"] = False
        self._cmake.definitions["ENABLE_EXTREME_NUMBERS"] = False
        self._cmake.definitions["ENABLE_METADATA_PERF_TESTS"] = False
        self._cmake.definitions["ENABLE_FSYNC"] = False # Option?
        self._cmake.definitions["ENABLE_JNA"] = False
        self._cmake.definitions["ENABLE_LARGE_FILE_SUPPORT"] = True # Option?
        self._cmake.definitions["ENABLE_EXAMPLE_TESTS"] = False
        self._cmake.definitions["ENABLE_PARALLEL4"] = self.options.get_safe("parallel", False)
        self._cmake.definitions["ENABLE_PNETCDF"] = False
        self._cmake.definitions["ENABLE_ERANGE_FILL"] = False
        self._cmake.definitions["ENABLE_PARALLEL_TESTS"] = False
        self._cmake.definitions["ENABLE_FILTER_TESTING"] = False
        self._cmake.definitions["ENABLE_CLIENTSIDE_FILTERS"] = False
        self._cmake.definitions["ENABLE_DOXYGEN"] = False
        self._cmake.definitions["ENABLE_DISKLESS"] = True
        if self.settings.compiler == "Visual Studio":
            self._cmake.definitions["NC_MSVC_STACK_SIZE"] = 40000000 # Option?
        self._cmake.definitions["ENABLE_CDF5"] = True
        self._cmake.definitions["ENABLE_BASH_SCRIPT_TESTING"] = False
        self._cmake.configure(build_folder=self._build_subfolder)
        return self._cmake

    def package(self):
        self.copy("COPYING", dst="licenses", src=self._source_subfolder)
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
        self.cpp_info.components["netcdf"].libs = tools.collect_libs(self)
        if self.options.get_safe("hdf4", False):
            self.cpp_info.components["netcdf"].requires.append("hdf4::hdf4")
        if self.options.get_safe("hdf5", False):
            self.cpp_info.components["netcdf"].requires.append("hdf5::hdf5") # TODO: when components available in hdf5 recipe => requires.extend([hdf5::hl, hdf5::c])
        if self.options.dap:
            self.cpp_info.components["netcdf"].requires.append("libcurl::libcurl")
        if self.options.get_safe("parallel", False):
            self.cpp_info.components["netcdf"].requires.append("openmpi::openmpi")
        if self.settings.os == "Linux":
            self.cpp_info.components["netcdf"].system_libs.append("m")
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.components["netcdf"].defines.append("DLL_NETCDF")
