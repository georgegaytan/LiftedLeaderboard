from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        # Use an ID logic if needed, but here we can let Postgres or Django handle or rely on a default ID.
        # Since Discord bot sets ID logic via discord IDs, a superuser won't have a discord ID naturally,
        # so we might need a fallback or fake ID. For now just set id=0 or something if it fails.
        # It's better to log in as an existing Discord user and make them an admin.
        # For createsuperuser script, we should override id if not provided.
        if 'id' not in extra_fields:
            # Generate a random big int if missing
            import random

            extra_fields['id'] = random.randint(10000000000000000, 99999999999999999)
        if 'display_name' not in extra_fields:
            extra_fields['display_name'] = email.split('@')[0]

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    id = models.BigIntegerField(primary_key=True)
    display_name = models.TextField()
    total_xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)

    email = models.EmailField(unique=True, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    class Meta:
        managed = False
        db_table = 'users'

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def __str__(self):
        return self.display_name or str(self.email)


class Activity(models.Model):
    name = models.TextField(unique=True)
    category = models.TextField()
    xp_value = models.IntegerField(default=0)
    is_archived = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'activities'

    def __str__(self):
        return self.name


class ActivityRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity = models.ForeignKey(Activity, on_delete=models.DO_NOTHING)
    note = models.TextField(null=True, blank=True)
    date_occurred = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        managed = False
        db_table = 'activity_records'

    def __str__(self):
        return f"{self.user} - {self.activity}"


class LevelThreshold(models.Model):
    level = models.IntegerField(primary_key=True)
    xp_required = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'level_thresholds'

    def __str__(self):
        return f"Level {self.level}"
