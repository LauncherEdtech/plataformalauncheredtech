from datetime import datetime
from app.extensions import db  # ajuste para o seu import
from flask_login import UserMixin

class OnboardingProgress(db.Model):
    __tablename__ = "onboarding_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False, index=True)

    step = db.Column(db.String(50), nullable=False, default="cronograma")  # etapa atual
    completed = db.Column(db.Boolean, nullable=False, default=False)
    skipped = db.Column(db.Boolean, nullable=False, default=False)

    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "step": self.step,
            "completed": self.completed,
            "skipped": self.skipped,
        }
