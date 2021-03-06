"""Tests for the js-regex library."""
# -*- coding: UTF-8 -*-

from __future__ import unicode_literals

import re
from sys import version_info as python_version

import pytest

import js_regex

PY2 = python_version.major == 2
SKIP_ON_PY2 = pytest.mark.skipif(PY2, reason="Not supported on Python 2")
SKIP_BEFORE_36 = pytest.mark.skipif(python_version < (3, 6), reason="also old")


@pytest.mark.parametrize(
    "pattern,good_match,bad_match",
    [
        ("^abc", "abc", ""),
        ("^abc", "abcd", "not abc"),
        ("^abc$", "abc", "abc\n"),
        ("^abc$|^def$", "abc", "abc\n"),
        ("^abc$|^def$", "def", "def\n"),
        (r"^abc\$", "abc$", "abc"),
        (r"\a", "\a", r"\a"),
        (r"\cA", "\x01", r"\cA"),
        (r"\ca", "\x01", r"\ca"),
    ],
)
def test_expected_transforms(pattern, good_match, bad_match):
    regex = js_regex.compile(pattern)
    assert regex.search(good_match)
    assert not regex.search(bad_match)


@pytest.mark.parametrize(
    "pattern,good_match,bad_match",
    [
        pytest.param(r"\d", "1", "߀", marks=SKIP_ON_PY2),  # NKO DIGIT ZERO
        (r"\D", "߀", "1"),
        pytest.param(r"\w", "a", "é", marks=SKIP_ON_PY2),  # Latin-1 e-acute
        (r"\W", "é", "a"),
        pytest.param(r"\s", "\t", "\xa0", marks=SKIP_ON_PY2),  # non-breaking space
        (r"\S", "\xa0", "\t"),
    ],
)
def test_charclass_transforms(pattern, good_match, bad_match):
    regex = js_regex.compile(pattern)
    assert regex.search(good_match)
    assert not regex.search(bad_match)
    if ord(bad_match) >= 128:
        # Non-ascii string is matched by Python 3, but not in JS mode
        assert re.compile(pattern).search(bad_match)


@pytest.mark.parametrize(
    "pattern,string",
    [
        ("a(?=b)", "ab"),
        ("a(?=b)", "ac"),
        ("(?<=a)b", "ab"),
        ("(?<=a)b", "ac"),
        ("a(?!b)", "ab"),
        ("a(?!b)", "ac"),
        ("(?<!a)b", "ab"),
        ("(?<!a)b", "ac"),
        ("a?", "abc"),
        ("a*", "abc"),
        ("a+", "abc"),
        ("a+?", "abc"),
        ("a{1,2}", "abc"),
        ("a?", "def"),
        ("a*", "def"),
        ("a+", "def"),
        ("a+?", "def"),
        ("a{1,2}", "def"),
    ],
)
def test_consistent_behaviour_is_consistent(pattern, string):
    # The main point of this test is to excercise the recursion in check_features
    convert = bool if PY2 else repr
    assert convert(re.search(pattern, string)) == convert(
        js_regex.compile(pattern).search(string)
    )


@pytest.mark.parametrize(
    "pattern,error",
    [
        (1, TypeError),
        (r"(abc(", re.error),
        (r"\A", js_regex.NotJavascriptRegex),
        (r"\Z", js_regex.NotJavascriptRegex),
        (r"(?#comment)", js_regex.NotJavascriptRegex),
        (r"(?#a different comment)", js_regex.NotJavascriptRegex),
        pytest.param(r"(?i:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?-i:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?m:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?-m:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?s:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?-s:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?x:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?-x:regex)", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        (r"(abc)(?(1)then|else)", js_regex.NotJavascriptRegex),
        # Defining a named capture group is checked separately to these named
        # references; it's therefore a Python-level error or a redundant test.
        (r"(?(name)then|else)", re.error),
        (r"(?P<name>regex)(?(name)then|else)", js_regex.NotJavascriptRegex),
        # Test that check_features recurses through all the things it should
        (r"a(?=\Z)", js_regex.NotJavascriptRegex),
        (r"(?<=\A)b", js_regex.NotJavascriptRegex),
        (r"a(?!\Z)", js_regex.NotJavascriptRegex),
        (r"(?<!\A)b", js_regex.NotJavascriptRegex),
        pytest.param(r"a|(?i:b)|c", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?i:regex)?", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(r"(?i:regex)+", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36),
        pytest.param(
            r"(?i:regex)+?", js_regex.NotJavascriptRegex, marks=SKIP_BEFORE_36
        ),
    ],
)
def test_pattern_validation(pattern, error):
    with pytest.raises(error):
        js_regex.compile(pattern)


@pytest.mark.parametrize(
    "flags,error",
    [
        ("flags", TypeError),
        (re.LOCALE, js_regex.NotJavascriptRegex),
        (re.TEMPLATE, js_regex.NotJavascriptRegex),
        (re.VERBOSE, js_regex.NotJavascriptRegex),
    ],
)
def test_flags_validation(flags, error):
    with pytest.raises(error):
        js_regex.compile("", flags=flags)
