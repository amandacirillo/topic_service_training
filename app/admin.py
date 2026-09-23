"""Minimal HTML admin UI: browse topic lists/topics and approve AI
suggestions. Intentionally simple (server-rendered Jinja, no JS framework) --
this mirrors a small internal tool, not a customer-facing product.
"""
from flask import Blueprint, redirect, render_template, request, url_for

from app.models import Topic, TopicList, db
from app.suggester import default_llm_client, suggest_topics

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
def index():
    lists = TopicList.query.order_by(TopicList.name).all()
    return render_template('admin/index.html', lists=lists)


@admin_bp.route('/lists/<int:list_id>')
def list_detail(list_id):
    topic_list = TopicList.query.get_or_404(list_id)
    topics = topic_list.topics.order_by(Topic.created_at.desc()).all()
    return render_template('admin/list_detail.html', topic_list=topic_list, topics=topics)


@admin_bp.route('/lists/<int:list_id>/suggest', methods=['GET', 'POST'])
def suggest(list_id):
    topic_list = TopicList.query.get_or_404(list_id)

    if request.method == 'POST':
        approved_texts = request.form.getlist('approved')
        for text in approved_texts:
            db.session.add(Topic(text=text, topic_list=topic_list))
        db.session.commit()
        return redirect(url_for('admin.list_detail', list_id=list_id))

    existing = [t.text for t in topic_list.topics]
    suggestions = suggest_topics(
        default_llm_client(), topic_list.name, topic_list.description, existing
    )
    return render_template(
        'admin/suggest.html', topic_list=topic_list, suggestions=suggestions
    )
