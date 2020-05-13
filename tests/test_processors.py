from unittest import mock
from websub.processors import Processor


def test_processor():
    use_case = mock.Mock()
    processor = Processor(use_case=use_case)
    assert iter(processor) == processor

    use_case.execute.return_value = False
    assert next(processor) is False
    use_case.execute.return_value = True
    assert next(processor) is True
    use_case.execute.return_value = None
    assert next(processor) is None
    use_case.execute.return_value = True
    use_case.execute.side_effect = Exception('Test')
    assert next(processor) is None
