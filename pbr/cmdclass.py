# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Utilities with minimum-depends for use in setup.py
"""

import os

from setuptools.command import sdist
from pbr import util


def parse_mailmap(mailmap='.mailmap'):
    mapping = {}
    if os.path.exists(mailmap):
        fp = open(mailmap, 'r')
        for l in fp:
            l = l.strip()
            if not l.startswith('#') and ' ' in l:
                canonical_email, alias = [x for x in l.split(' ')
                                          if x.startswith('<')]
                mapping[alias] = canonical_email
    return mapping


def canonicalize_emails(changelog, mapping):
    """Takes in a string and an email alias mapping and replaces all
       instances of the aliases in the string with their real email.
    """
    for alias, email in mapping.iteritems():
        changelog = changelog.replace(alias, email)
    return changelog


def write_git_changelog():
    """Write a changelog based on the git changelog."""
    if os.path.isdir('.git'):
        git_log_cmd = 'git log --stat'
        changelog = util.run_shell_command(git_log_cmd)
        mailmap = parse_mailmap()
        with open("ChangeLog", "w") as changelog_file:
            changelog_file.write(canonicalize_emails(changelog, mailmap))


def generate_authors():
    """Create AUTHORS file using git commits."""
    jenkins_email = 'jenkins@review.openstack.org'
    old_authors = 'AUTHORS.in'
    new_authors = 'AUTHORS'
    if os.path.isdir('.git'):
        # don't include jenkins email address in AUTHORS file
        git_log_cmd = ("git log --format='%aN <%aE>' | sort -u | "
                       "grep -v " + jenkins_email)
        author_entries = util.run_shell_command(git_log_cmd).split("\n")
        signed_cmd = "git log | grep Co-authored-by: | sort -u"
        signed_entries = util.run_shell_command(signed_cmd)
        if signed_entries:
            author_entries.extend([signed.split(":", 1)[1].strip()
                                   for signed in signed_entries.split("\n")])
        mailmap = parse_mailmap()
        authors = list(set([canonicalize_emails(author, mailmap)
                            for author in author_entries]))
        authors.sort()
        with open(new_authors, 'w') as new_authors_fh:
            new_authors_fh.write("\n".join(authors))
            if os.path.exists(old_authors):
                with open(old_authors, "r") as old_authors_fh:
                    new_authors_fh.write('\n' + old_authors_fh.read())


_rst_template = """%(heading)s
%(underline)s

.. automodule:: %(module)s
  :members:
  :undoc-members:
  :show-inheritance:
"""


def get_cmdclass(versioninfo_path):
    """Return dict of commands to run from setup.py."""

    cmdclass = dict()

    def _find_modules(arg, dirname, files):
        for filename in files:
            if filename.endswith('.py') and filename != '__init__.py':
                arg["%s.%s" % (dirname.replace('/', '.'),
                               filename[:-3])] = True

    class LocalSDist(sdist.sdist):
        """Builds the ChangeLog and Authors files from VC first."""

        def check_readme(self):
            alts = ("README.rst", "README", "README.txt")
            for f in alts:
                if os.path.exists(f):
                    return
            else:
                self.warn(
                    "standard file not found: should have one of " +
                    ', '.join(alts)
                )

        def run(self):
            write_git_changelog()
            generate_authors()
            have_template = os.path.exists(self.template)
            if not have_template:
                with open(self.template, 'w') as template:
                    template.write("""
include AUTHORS
include ChangeLog
include %s
exclude .gitignore
exclude .gitreview
""" % versioninfo_path)
            # sdist.sdist is an old style class, can't use super()
            sdist.sdist.run(self)
            if not have_template:
                os.remove(self.template)

    cmdclass['sdist'] = LocalSDist

    # If Sphinx is installed on the box running setup.py,
    # enable setup.py to build the documentation, otherwise,
    # just ignore it
    try:
        from sphinx.setup_command import BuildDoc

        class LocalBuildDoc(BuildDoc):
            def generate_autoindex(self):
                print "**Autodocumenting from %s" % os.path.abspath(os.curdir)
                modules = {}
                source_dir = os.path.join(self.source_dir, 'api')
                if not os.path.exists(source_dir):
                    self.mkpath(source_dir)
                for pkg in self.distribution.packages:
                    if '.' not in pkg:
                        os.path.walk(pkg, _find_modules, modules)
                module_list = modules.keys()
                module_list.sort()
                autoindex_filename = os.path.join(source_dir, 'autoindex.rst')
                with open(autoindex_filename, 'w') as autoindex:
                    autoindex.write(""".. toctree::
   :maxdepth: 1

""")
                    for module in module_list:
                        output_filename = os.path.join(source_dir,
                                                       "%s.rst" % module)
                        heading = "The :mod:`%s` Module" % module
                        underline = "=" * len(heading)
                        values = dict(module=module, heading=heading,
                                      underline=underline)

                        print "Generating %s" % output_filename
                        with open(output_filename, 'w') as output_file:
                            output_file.write(_rst_template % values)
                        autoindex.write("   %s.rst\n" % module)

            def initialize_options(self):
                BuildDoc.initialize_options(self)
                # Fix up defaults for option dicts
                build_doc = self.distribution.get_option_dict('build_sphinx')
                if 'source_dir' not in build_doc:
                    self.source_dir = 'doc/source'
                if 'build_dir' not in build_doc:
                    self.build_dir = 'doc/build'
                self.all_files = False

            def run(self):
                if not os.getenv('SPHINX_DEBUG'):
                    self.generate_autoindex()

                for builder in ['html', 'man']:
                    self.builder = builder
                    self.finalize_options()
                    self.project = self.distribution.get_name()
                    self.version = self.distribution.get_version()
                    self.release = self.distribution.get_version()
                    BuildDoc.run(self)
        cmdclass['build_sphinx'] = LocalBuildDoc
    except ImportError:
        pass

    try:
        from setuptools.command.upload_docs import upload_docs

        class LocalUploadDocs(upload_docs):
            def run(self):
                build_dict = self.distribution.get_option_dict('build_sphinx')
                if 'build_dir' in build_dict:
                    html_dir = os.path.join(build_dict['build_dir'][1], 'html')
                else:
                    html_dir = 'doc/build/html'
                upload_doc = self.distribution.get_option_dict('upload_docs')
                upload_doc['upload_dir'] = ('pbr', html_dir)
                self.distribution.command_options['upload_docs'] = upload_doc
                upload_docs.run(self)
        cmdclass['upload_docs'] = LocalUploadDocs
    except ImportError:
        pass

    return cmdclass
