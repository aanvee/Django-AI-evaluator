from django.db.models.signals import post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from .models import Submission

@receiver(post_save, sender=Submission)
def trigger_feedback_generation(sender, instance, created, **kwargs):
    # Only generate feedback if it's a new submission or if score is set but feedback is missing
    if created or (instance.score is not None and not instance.feedback):
        # Prevent recursion by checking if feedback is already being generated or exists
        if not instance.feedback:
            async_task('evaluator.services.feedback_service.generate_feedback_task', instance.id)
