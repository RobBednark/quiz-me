from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, password=None):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
                email=UserManager.normalize_email(email),
        )
        user.set_password(password)
        user.save(using=self._db) 
        return user

    def create_superuser(self, email, password):
        """
        Creates and saves a superuser with the given email and password.
        """
        user = self.create_user(
                    email,
                    password=password,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        db_index=True,
    )
    is_active = models.BooleanField(default=True) 
    is_admin = models.BooleanField(default=False)
    # answer_set = ForeignKey(Answer)
    # attempt_set = ForeignKey(Attempt)
    # hint_set = ForeignKey(Hint)
    # question_set = ForeignKey(Question)
    # questiontag_set = ForeignKey(QuestionTag)
    # quiz_set = ForeignKey(Quiz)
    # tag_set = ManyToMany(Tag)
    # usertag_set = ForeignKey(UserTag)

    objects = UserManager() 
    USERNAME_FIELD = 'email'
    # REQUIRED_FIELDS specifies fields that must be provided when creating a user
    REQUIRED_FIELDS = []

    def get_full_name(self):
        # The user is identified by their email address 
        return self.email

    def get_short_name(self):
        # The user is identified by their email address 
        return self.email

    def __unicode__(self): 
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?" 
        # Simplest possible answer: Yes, always 
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app 'app_label'?" 
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
