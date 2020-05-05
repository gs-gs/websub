import pytest
from websub.use_cases import SubscriptionRegisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*", 1000,)


def test_execute(subscription_repo):
    subscription_repo.post.return_value = True
    uc = SubscriptionRegisterUseCase()
    assert uc.execute(*USE_CASE_ARGS)

    subscription_repo.post.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(subscription_repo.post.side_effect)

    subscription_repo.post.side_effect = None
    subscription_repo.post.return_value = None
    assert uc.execute(*USE_CASE_ARGS) is None
    assert subscription_repo.post.call_count == 3
