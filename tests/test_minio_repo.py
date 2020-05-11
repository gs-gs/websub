from unittest import TestCase

import pytest

from websub.repos import Pattern


class MinioPatternTest(TestCase):
    def test_to_key__when_empty__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='').to_key()

    def test_to_key__when_contains_slashes__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='aa/bb').to_key()

    def test_to_key__when_wildcard_without_dot__should_return_error(self):
        with pytest.raises(ValueError):
            Pattern(predicate='aa.bb*').to_key()

    def test_to_key__when_predicate_valid__should_return_key(self):
        assert Pattern('aaaa.bbbb.cccc').to_key() == "AAAA/BBBB/CCCC/"

    def test_to_key__with_wildcard_in_predicate__should_be_handled(self):
        assert Pattern('aaaa.bbbb.cccc.*').to_key() == "AAAA/BBBB/CCCC/"
        assert Pattern('aaaa.bbbb.cccc.').to_key() == "AAAA/BBBB/CCCC/"

    def test_to_layers__should_return_list_of_layers(self):
        assert Pattern('aaaa.bbbb.cccc.*').to_layers() == [
            'AAAA/',
            'AAAA/BBBB/',
            'AAAA/BBBB/CCCC/'
        ]
