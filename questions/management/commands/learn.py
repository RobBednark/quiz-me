from django.core.management.base import NoArgsCommand
import questions.models as models

class Command(NoArgsCommand):
    help = "run this script"

    def handle_noargs(self, **options):
        questions = models.Question.objects.all()
        tags = models.Tag.objects.all()
        question_tags = models.QuestionTag.objects.all()
        user_tags = models.UserTag.objects.all()
        user = models.User.objects.all()[0]
        user_tags = models.UserTag.objects.filter(enabled=True, user=user)
        question_tags = models.QuestionTag.objects.filter(tag__in=user_tags, enabled=True)

        import pdb; pdb.set_trace()
        pass
