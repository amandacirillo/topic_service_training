"""Unauthenticated health/info endpoints for load balancer checks and
smoke-testing a deployment."""
from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
@health_bp.route('/healthz')
def health():
    return jsonify({'status': 'ok'})


@health_bp.route('/info')
def info():
    from app.models import Topic, TopicList

    return jsonify({
        'service': 'topic-service-training',
        'topic_list_count': TopicList.query.count(),
        'topic_count': Topic.query.count(),
    })
