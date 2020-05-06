import pytest
from websub.use_cases import SubscriptionDeregisterUseCase

USE_CASE_ARGS = ("http://url.com/callback", "UN.CEFACT.*")


def test_execute(subscriptions_repo):
    subscriptions_repo.delete.return_value = 1
    uc = SubscriptionDeregisterUseCase()
    assert uc.execute(*USE_CASE_ARGS)

    subscriptions_repo.delete.side_effect = Exception("Hey")
    with pytest.raises(Exception) as e:
        uc.execute(*USE_CASE_ARGS)
        assert str(e) == str(subscriptions_repo.post.side_effect)

    subscriptions_repo.delete.side_effect = None
    subscriptions_repo.delete.return_value = 0
    assert not uc.execute(*USE_CASE_ARGS)
    assert subscriptions_repo.delete.call_count == 3
