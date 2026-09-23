"""SQLAlchemy models for topic lists, topics, and usage history."""
import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


class TopicList(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'topic_lists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(256), unique=True, nullable=False)
    description = db.Column(db.String(5000), nullable=True)
    # If reusable=False, a topic is deactivated the moment it's served once --
    # useful for "queue of one-time-use items" lists rather than a rotating pool.
    reusable = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    topics = db.relationship('Topic', backref='topic_list', cascade='all, delete-orphan', lazy='dynamic')

    def active_count(self) -> int:
        return self.topics.filter_by(is_active=True).count()

    def total_count(self) -> int:
        return self.topics.count()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'reusable': self.reusable,
            'topic_count': self.total_count(),
            'active_count': self.active_count(),
        }


class Topic(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'topics'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(5000), nullable=False)
    category = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    topic_list_id = db.Column(db.Integer, db.ForeignKey('topic_lists.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    usages = db.relationship('TopicUsage', backref='topic', cascade='all, delete-orphan', lazy='dynamic')

    def usage_count(self) -> int:
        return self.usages.count()

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'text': self.text,
            'category': self.category,
            'active': self.is_active,
            'topic_list_id': self.topic_list_id,
            'topic_list_name': self.topic_list.name if self.topic_list else None,
            'uses': self.usage_count(),
            'created_at': self.created_at.isoformat(),
        }


class TopicUsage(db.Model):  # type: ignore[name-defined]
    __tablename__ = 'topic_usages'

    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), nullable=False)
    used_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
