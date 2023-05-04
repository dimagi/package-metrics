import json
from json import JSONDecodeError

import sh

from dependency_metrics.constants import UNKNOWN_VERSION
from dependency_metrics.exceptions import Crash


def get_yarn_packages():
    version = Yarn.version()
    if not version.startswith("1."):
        raise Crash(f"Yarn Classic (v1.x) is required, found {version}")

    outdated_packages = []
    for package in parse_yarn_list():
        latest_version = pull_latest_version(package["name"])
        if package["version"] != latest_version:
            # only care if it is actually outdated
            package["latest_version"] = latest_version
            outdated_packages.append(package)
    return outdated_packages


def pull_latest_version(package_name):
    """
    Attempts to pull latest version of package from yarn
    :param package_name: name of javascript package
    :returns: returns version as string, or UNKNOWN_VERSION if not found
    """
    string_output = Yarn.latest_version(package_name)
    if not string_output:
        return UNKNOWN_VERSION

    try:
        json_output = json.loads(string_output)
    except JSONDecodeError:
        return UNKNOWN_VERSION

    if json_output.get('type') == 'inspect':
        return json_output.get('data')

    return UNKNOWN_VERSION


def parse_yarn_list():
    """
    Parse output of ``Yarn.list`` into list of package name and version dicts
    """
    packages = []
    yarn_list = Yarn.list()
    # trim first and last line from output as they are irrelevant
    for line in yarn_list.splitlines()[1:-1]:
        line = line.rstrip()
        if not line:
            continue
        # example:
        # ├─ @ungap/promise-all-settled@1.1.2
        # ├─ abbrev@1.1.1
        name, x, version = line.split(None, 2)[1].rpartition("@")
        packages.append({"name": name, "version": version})
    return packages


class Yarn:
    """
    Class to house raw yarn commands
    """

    @staticmethod
    def latest_version(package_name):
        """
        Equivalent to ``yarn info <package_name> dist-tags.latest --json``
        """
        return sh.yarn("info", package_name, "dist-tags.latest", "--json")

    @staticmethod
    def list():
        """
        Equivalent to ``yarn list --depth 0``
        """
        return sh.yarn("list", "--depth", "0")

    @staticmethod
    def version():
        """
        Equivalent to ``yarn --version``
        """
        return sh.yarn("--version")
