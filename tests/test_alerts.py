from app.alerts import NullNotificationSender, is_low_inventory, maybe_alert
from app.models import Topic, TopicList, db


def make_list(app, name='One-time prompts', reusable=False, active=2, inactive=8):
    with app.app_context():
        topic_list = TopicList(name=name, reusable=reusable)
        db.session.add(topic_list)
        db.session.flush()
        for i in range(active):
            db.session.add(Topic(text=f'active-{i}', topic_list_id=topic_list.id, is_active=True))
        for i in range(inactive):
            db.session.add(Topic(text=f'inactive-{i}', topic_list_id=topic_list.id, is_active=False))
        db.session.commit()
        return topic_list.id


def test_is_low_inventory_true_when_below_absolute_threshold():
    assert is_low_inventory(active_count=5, total_count=100) is True


def test_is_low_inventory_true_when_below_percent_threshold():
    # 15/100 = 15% active is below default 10%? no -- craft a clearer case:
    assert is_low_inventory(active_count=2, total_count=100) is True


def test_is_low_inventory_false_when_healthy():
    assert is_low_inventory(active_count=50, total_count=100) is False


def test_is_low_inventory_handles_empty_list():
    assert is_low_inventory(active_count=0, total_count=0) is False


def test_maybe_alert_skips_reusable_lists(app):
    list_id = make_list(app, reusable=True, active=1, inactive=99)
    with app.app_context():
        topic_list = db.session.get(TopicList, list_id)
        sender = NullNotificationSender()
        sent = maybe_alert(topic_list, sender)
    assert sent is False
    assert sender.sent == []


def test_maybe_alert_sends_for_low_non_reusable_list(app):
    list_id = make_list(app, reusable=False, active=1, inactive=99)
    with app.app_context():
        topic_list = db.session.get(TopicList, list_id)
        sender = NullNotificationSender()
        sent = maybe_alert(topic_list, sender)
        assert sent is True
        assert len(sender.sent) == 1
        subject, body = sender.sent[0]
        assert topic_list.name in subject


def test_maybe_alert_no_op_when_inventory_healthy(app):
    list_id = make_list(app, reusable=False, active=90, inactive=10)
    with app.app_context():
        topic_list = db.session.get(TopicList, list_id)
        sender = NullNotificationSender()
        sent = maybe_alert(topic_list, sender)
    assert sent is False
    assert sender.sent == []
