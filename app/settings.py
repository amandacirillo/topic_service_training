"""App-wide configuration, read from environment variables."""
import os


class Settings:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL', 'sqlite:///topics.db')
        self.api_key = os.environ.get('API_KEY', 'local-dev-key')
        self.low_inventory_absolute = int(os.environ.get('LOW_INVENTORY_ABSOLUTE', '10'))
        self.low_inventory_percent = float(os.environ.get('LOW_INVENTORY_PERCENT', '0.10'))
        self.alert_email_to = os.environ.get('ALERT_EMAIL_TO', 'alerts@example.com')
        self.alert_email_from = os.environ.get('ALERT_EMAIL_FROM', 'topic-service@example.com')
        self.aws_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
        self.llm_model = os.environ.get('LLM_MODEL', 'gpt-4o')
        self.flask_debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'


settings = Settings()
