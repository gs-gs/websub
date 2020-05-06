import pytest
from websub.use_cases import SubscriptionRegisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*", 1000,)


def test_execute(subscriptions_repo):
    subscriptions_repo.post.return_value = True
    uc = SubscriptionRegisterUseCase()
    assert uc.execute(*USE_CASE_ARGS)

    subscriptions_repo.post.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(subscriptions_repo.post.side_effect)

    subscriptions_repo.post.side_effect = None
    subscriptions_repo.post.return_value = None
    assert uc.execute(*USE_CASE_ARGS) is None
    assert subscriptions_repo.post.call_count == 3
