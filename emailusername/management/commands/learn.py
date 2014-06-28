from django.core.management.base import NoArgsCommand
import myapp.models as models

class Command(NoArgsCommand):
    help = "run this script"

    def handle_noargs(self, **options):
        questions = models.Question.objects.all()
        tags = models.Tag.objects.all()
        question_tags = models.QuestionTag.objects.all()
        user_tags = models.UserTag.objects.all()
        import pdb; pdb.set_trace()
        pass
