"""JSON API: manage topic lists/topics and serve the next topic."""
from flask import Blueprint, current_app, jsonify, request

from app.alerts import NullNotificationSender, SesNotificationSender, maybe_alert
from app.auth import require_api_key
from app.models import Topic, TopicList, TopicUsage, db
from app.strategies import DEFAULT_STRATEGY, STRATEGIES, select

api_bp = Blueprint('api', __name__, url_prefix='/api')


def _notification_sender():
    # In TESTING (and local DEBUG) mode we never want a real SES call to
    # fire, so route through the in-memory fake instead. A more elaborate
    # app could register the sender on app.extensions at factory time; this
    # simple config check is enough for a training example.
    if current_app.testing or current_app.debug:
        return NullNotificationSender()
    return SesNotificationSender()


@api_bp.route('/topic_lists', methods=['GET'])
@require_api_key
def list_topic_lists():
    lists = TopicList.query.order_by(TopicList.name).all()
    return jsonify([tl.to_dict() for tl in lists])


@api_bp.route('/topic_lists', methods=['POST'])
@require_api_key
def create_topic_list():
    payload = request.get_json(force=True, silent=True) or {}
    name = (payload.get('name') or '').strip()
    if not name:
        return jsonify({'error': 'name is required'}), 400
    if TopicList.query.filter_by(name=name).first():
        return jsonify({'error': f'topic list "{name}" already exists'}), 409

    topic_list = TopicList(
        name=name,
        description=payload.get('description'),
        reusable=bool(payload.get('reusable', True)),
    )
    db.session.add(topic_list)
    db.session.commit()
    return jsonify(topic_list.to_dict()), 201


@api_bp.route('/topic_lists/<int:list_id>/topics', methods=['POST'])
@require_api_key
def add_topic(list_id):
    topic_list = TopicList.query.get_or_404(list_id)
    payload = request.get_json(force=True, silent=True) or {}
    text = (payload.get('text') or '').strip()
    if not text:
        return jsonify({'error': 'text is required'}), 400

    topic = Topic(text=text, category=payload.get('category'), topic_list=topic_list)
    db.session.add(topic)
    db.session.commit()
    return jsonify(topic.to_dict()), 201


@api_bp.route('/topic_lists/<int:list_id>/next_topic', methods=['GET'])
@require_api_key
def next_topic(list_id):
    topic_list = TopicList.query.get_or_404(list_id)
    strategy_name = request.args.get('strategy', DEFAULT_STRATEGY)
    if strategy_name not in STRATEGIES:
        return jsonify({'error': f'unknown strategy "{strategy_name}"'}), 400

    candidates = topic_list.topics.filter_by(is_active=True).all()
    chosen = select(strategy_name, candidates)
    if chosen is None:
        return jsonify({'error': 'no active topics available in this list'}), 404

    db.session.add(TopicUsage(topic_id=chosen.id))
    if not topic_list.reusable:
        chosen.is_active = False
    db.session.commit()

    maybe_alert(topic_list, _notification_sender())

    return jsonify(chosen.to_dict())


@api_bp.route('/topics/<int:topic_id>/deactivate', methods=['POST'])
@require_api_key
def deactivate_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    topic.is_active = False
    db.session.commit()
    return jsonify(topic.to_dict())
