from conan import ConanFile
from conan.errors import ConanInvalidConfiguration
from conan.tools.build import check_min_cppstd
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.env import VirtualBuildEnv
from conan.tools.files import apply_conandata_patches, copy, export_conandata_patches, get, replace_in_file, rm, rmdir
from conan.tools.microsoft import check_min_vs, is_msvc, is_msvc_static_runtime
from conan.tools.scm import Version
import os


required_conan_version = ">=1.53.0"

#
# INFO: Please, remove all comments before pushing your PR!
#


class PfsConan(ConanFile):
    name = "pfs"
    description = "procfs parsing library in C++"
    license = "Apache-2.0"
    url = "https://github.com/conan-io/conan-center-index"
    homepage = "https://github.com/dtrugman/pfs"
    topics = ("linux", "programming", "cpp", "procfs", "cpp-library")
    package_type = "library"
    settings = "os", "arch", "compiler", "build_type"
    options = {
        "shared": [True, False],
        "fPIC": [True, False],
        "asan": [True, False],
        "build_samples": [True, False],
        "build_tests": [True, False],
        "coverage": [True, False],
    }
    default_options = {
        "shared": False,
        "fPIC": True,
        "asan": False,
        "build_samples": True,
        "build_tests": True,
        "coverage": False,
    }

    @property
    def _min_cppstd(self):
        return 11

    def export_sources(self):
        export_conandata_patches(self)

    def config_options(self):
        if self.settings.os == "Windows":
            del self.options.fPIC

    def configure(self):
        if self.options.shared:
            self.options.rm_safe("fPIC")

    def layout(self):
        cmake_layout(self, src_folder="src")

    def validate(self):
        if self.settings.compiler.cppstd:
            check_min_cppstd(self, self._min_cppstd)
        if self.settings.os not in ["Linux", "iOS", "watchOS", "tvOS", "visionOS", "Macos", "Android", "FreeBSD", "SunOS", "AIX", "Arduino", "Neutrino", "baremetal", "VxWorks"]:
            raise ConanInvalidConfiguration(f"{self.ref} is not supported on {self.settings.os}.")

    def source(self):
        get(self, **self.conan_data["sources"][self.version], strip_root=True)
        self._patch_sources()

    def generate(self):
        tc = CMakeToolchain(self)
        tc.variables["pfs_BUILD_ASAN"] = self.options.asan
        tc.variables["pfs_BUILD_COVERAGE"] = self.options.coverage
        tc.variables["pfs_BUILD_SAMPLES"] = self.options.build_samples
        tc.variables["pfs_BUILD_TESTS"] = self.options.build_tests
        tc.generate()

        tc = CMakeDeps(self)
        tc.generate()

    def _patch_sources(self):
        apply_conandata_patches(self)

    def build(self):
        if self.settings.os == "Android":
            replace_in_file(self, os.path.join(self.source_folder, "CMakeLists.txt"),
                            "target_link_libraries (unittest PRIVATE pfs)",
                            "target_link_libraries (unittest PRIVATE pfs -llog)")
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        copy(self, "LICENSE", self.source_folder, os.path.join(self.package_folder, "licenses"))
        cmake = CMake(self)
        cmake.install()

        rmdir(self, os.path.join(self.package_folder, "lib", "pkgconfig"))
        rmdir(self, os.path.join(self.package_folder, "lib", "cmake"))
        rmdir(self, os.path.join(self.package_folder, "share"))
        rm(self, "*.la", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "lib"))
        rm(self, "*.pdb", os.path.join(self.package_folder, "bin"))

    def package_info(self):
        self.cpp_info.libs = ["pfs"]

        # if self.settings.os == "Android":
        #     self.cpp_info.system_libs.append("log")
        # If they are needed on Linux, m, pthread and dl are usually needed on FreeBSD too
        # if self.settings.os in ["Linux", "FreeBSD"]:
        #     self.cpp_info.system_libs.append("m")
        #     self.cpp_info.system_libs.append("pthread")
        #     self.cpp_info.system_libs.append("dl")
