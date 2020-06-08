import os

from conans import ConanFile, CMake, tools

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
        "hdf4": [True, False],
        "netcdf_4": [True, False],
        "hdf5": [True, False],
        "dap": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "hdf4": False,
        "netcdf_4": True,
        "hdf5": True,
        "dap": True,
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

    def requirements(self):
        if self.options.hdf4:
            self.requires("hdf4/4.2.15")
        if self.options.hdf5:
            self.requires("hdf5/1.12.0") # must be built with zlib and hl
        if self.options.dap:
            self.requires("libcurl/7.70.0")

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
        self._cmake.definitions["ENABLE_V2_API"] = True
        self._cmake.definitions["BUILD_UTILITIES"] = False
        self._cmake.definitions["ENABLE_MMAP"] = True
        self._cmake.definitions["ENABLE_EXAMPLES"] = False
        self._cmake.definitions["ENABLE_HDF4"] = self.options.hdf4
        if self.options.hdf4:
            self._cmake.definitions["ENABLE_HDF4_FILE_TESTS"] = False
        self._cmake.definitions["ENABLE_NETCDF_4"] = self.options.netcdf_4
        self._cmake.definitions["ENABLE_LOGGING"] = False
        self._cmake.definitions["ENABLE_SET_LOG_LEVEL_FUNC"] = True
        self._cmake.definitions["ENABLE_STRICT_NULL_BYTE_HEADER_PADDING"] = False
        self._cmake.definitions["ENABLE_RPC"] = False
        self._cmake.definitions["USE_HDF5"] = self.options.hdf5
        if self.options.hdf5:
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
        self._cmake.definitions["ENABLE_FSYNC"] = False
        self._cmake.definitions["ENABLE_JNA"] = False
        self._cmake.definitions["ENABLE_LARGE_FILE_SUPPORT"] = True
        self._cmake.definitions["ENABLE_EXAMPLE_TESTS"] = False
        self._cmake.definitions["ENABLE_PARALLEL4"] = self.options.hdf5
        self._cmake.definitions["ENABLE_PNETCDF"] = False
        self._cmake.definitions["ENABLE_ERANGE_FILL"] = False
        self._cmake.definitions["ENABLE_PARALLEL_TESTS"] = False
        self._cmake.definitions["ENABLE_FILTER_TESTING"] = False
        self._cmake.definitions["ENABLE_CLIENTSIDE_FILTERS"] = False
        self._cmake.definitions["ENABLE_DOXYGEN"] = False
        self._cmake.definitions["ENABLE_DISKLESS"] = True
        if self.settings.compiler == "Visual Studio":
            self._cmake.definitions["NC_MSVC_STACK_SIZE"] = 40000000
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
        self.cpp_info.libs = tools.collect_libs(self)
        if self.settings.os == "Linux":
            self.cpp_info.system_libs.append("m")
        if self.settings.os == "Windows" and self.options.shared:
            self.cpp_info.defines.append("DLL_NETCDF")
