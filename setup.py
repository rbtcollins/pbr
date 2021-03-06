# Copyright 2011 OpenStack, LLC
# Copyright 2012 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import setuptools

import pbr
import pbr.cmdclass
import pbr.requires

setuptools.setup(
    name="pbr",
    version=pbr.version_info.canonical_version_string(),
    author='Hewlett-Packard Development Company, L.P.',
    author_email='openstack@lists.launchpad.net',
    description="Python Build Reasonableness",
    license="Apache License, Version 2.0",
    url="https://github.com/openstack-dev/pbr",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=pbr.requires.parse_requirements('tools/pip-requires'),
    cmdclass=pbr.cmdclass.get_cmdclass('pbr/versioninfo'),
    classifiers=[
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
        "Programming Language :: Python"
    ],
    entry_points={
        "distutils.setup_keywords": [
            "version = pbr.hooks:inject_version",
            "install_requires = pbr.hooks:inject_requires",
            "dependency_links = pbr.hooks:inject_dependency_links",
        ]
    }
)
