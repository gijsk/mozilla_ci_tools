"""
This file contains tests for mozci/platforms.py.

We use a mapping generated by a version with triggers
allthethings.json and compare this with the results we get
from platforms.py.
"""
import json
import os
import pytest
import unittest

from mock import patch

import mozci.sources.allthethings
import mozci.platforms


def _update_json():
    """Update test_platforms.json to remove old test cases."""
    filepath = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "test_platforms.json"
    )
    with open(filepath, 'r') as f:
        reference_builders_info = json.load(f)

    builders_data = mozci.sources.allthethings.fetch_allthethings_data()['builders']

    for builder in reference_builders_info.keys():
        if builder not in builders_data:
            del reference_builders_info[builder]

    return reference_builders_info


def complex_data():
    """Build array of test cases from test_platforms.json."""
    reference_builders_info = _update_json()

    # The values of all the builds can be obtained by using .values()
    # on the data from test_platforms.json. When asking
    # determine_upstream_builder() for a builder we return itself. We add known
    # build jobs to reference_builders_info
    build_jobs = set(reference_builders_info.values())
    for build_job in build_jobs:
        reference_builders_info[build_job] = build_job

    tests = []
    for builder in reference_builders_info.keys():
        expected = reference_builders_info[builder]
        tests.append((builder, expected))

    return tests


def list_untested():
    """List untested buildernames."""
    t = set(_update_json())
    s = set(mozci.sources.allthethings.list_builders())
    with open('untested_builders.txt', 'w') as f:
        for x in sorted(s.difference(t)):
            f.write(x + '\n')

list_untested()


@pytest.mark.parametrize("builder, expected", complex_data())
def test_builders(builder, expected):
    """Individually test every pair returned by complex_data()."""
    obtained = mozci.platforms.determine_upstream_builder(builder)
    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)


def test_builders_error():
    """determine_upstream_builder should raise an Exception when no build job is found."""
    with pytest.raises(Exception):
        mozci.platforms.determine_upstream_builder("Not a valid buildername")

is_downstream_test_cases = [
    ("Linux mozilla-central pgo-build", False),
    ("Android armv7 API 11+ try debug build", False),
    ("b2g_try_linux64_gecko-debug build", False),
    ("b2g_ubuntu32_vm gaia-try opt test mochitest-1", False),
    ("Android 4.0 armv7 API 11+ mozilla-central debug test jsreftest-1", True)]


@pytest.mark.parametrize("builder, expected", is_downstream_test_cases)
def test_is_downstream(builder, expected):
    """Test is_dowstream with test cases from is_downstream_test_cases."""
    obtained = mozci.platforms.is_downstream(builder)
    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)

get_test_test_cases = [
    ("Windows 8 64-bit mozilla-aurora pgo talos dromaeojs", "dromaeojs"),
    ("Android 2.3 Emulator mozilla-release opt test plain-reftest-7", "plain-reftest-7")]


@pytest.mark.parametrize("test, expected", get_test_test_cases)
def test_get_test(test, expected):
    """Test _get_test with test cases from get_test_test_cases."""
    obtained = mozci.platforms._get_test(test)
    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)

get_platform_test_cases = [
    ("Ubuntu HW 12.04 mozilla-aurora talos svgr", "linux"),
    ("Android armv7 API 9 try opt test xpcshell-2", "android-api-9"),
    ("Android armv7 API 9 mozilla-release build", "android-api-9")]


@pytest.mark.parametrize("builder, expected", get_platform_test_cases)
def test_get_associated_platform_name(builder, expected):
    """Test get_associated_platform_name() with test cases from get_platform_test_cases."""
    obtained = mozci.platforms.get_associated_platform_name(builder)
    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)


def test_build_tests_per_platform_graph():
    """Test that build_tests_per_platform_graph correctly maps platforms to tests."""
    BUILDERS = ["Ubuntu HW 12.04 mozilla-aurora talos svgr",
                "Ubuntu VM 12.04 b2g-inbound debug test xpcshell",
                "Linux mozilla-aurora leak test build"]
    obtained = mozci.platforms.build_tests_per_platform_graph(BUILDERS)
    expected = {'debug': {'linux':
                          {'tests': ['xpcshell'],
                           'Linux b2g-inbound leak test build':
                           ['Ubuntu VM 12.04 b2g-inbound debug test xpcshell'],
                           'Linux mozilla-aurora leak test build': []}},
                'opt': {'linux':
                        {'tests': ['svgr'],
                         'Linux mozilla-aurora build':
                         ['Ubuntu HW 12.04 mozilla-aurora talos svgr']}}}

    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)


def test_filter_builders_matching():
    """Test that _filter_builders_matching correctly filters builds."""
    BUILDERS = ["Ubuntu HW 12.04 mozilla-aurora talos svgr",
                "Ubuntu VM 12.04 b2g-inbound debug test xpcshell"]
    obtained = mozci.platforms._filter_builders_matching(BUILDERS, " talos ")
    expected = ["Ubuntu HW 12.04 mozilla-aurora talos svgr"]
    assert obtained == expected, \
        'obtained: "%s", expected "%s"' % (obtained, expected)


class TestTalosBuildernames(unittest.TestCase):

    """We need this class because of the mock module."""

    @patch('mozci.platforms.fetch_allthethings_data')
    def test_talos_buildernames(self, fetch_allthethings_data):
        """Test build_talos_buildernames_for_repo with mock data."""
        fetch_allthethings_data.return_value = {
            'builders':
            {'PlatformA try talos buildername': {},
             'PlatformB try talos buildername': {},
             'PlatformA try pgo talos buildername': {},
             'Platform try buildername': {}}}
        self.assertEquals(mozci.platforms.build_talos_buildernames_for_repo('try'),
                          ['PlatformA try talos buildername',
                           'PlatformB try talos buildername'])
        self.assertEquals(mozci.platforms.build_talos_buildernames_for_repo('try', True),
                          ['PlatformA try pgo talos buildername',
                           'PlatformB try talos buildername'])
        self.assertEquals(mozci.platforms.build_talos_buildernames_for_repo('not-a-repo'), [])
