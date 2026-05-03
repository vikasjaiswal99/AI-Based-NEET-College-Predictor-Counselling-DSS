"""apps/accounts/models.py — Custom User + StudentProfile"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        if not email:
            raise ValueError('Email is required.')
        email = self.normalize_email(email)
        extra.setdefault('is_active', True)
        user = self.model(email=email, **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra):
        extra.setdefault('is_staff', True)
        extra.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra)


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT    = 'student',    _('Student')
        COUNSELLOR = 'counsellor', _('Counsellor')
        ADMIN      = 'admin',      _('Admin')

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email       = models.EmailField(unique=True)
    first_name  = models.CharField(max_length=60)
    last_name   = models.CharField(max_length=60)
    role        = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()
    USERNAME_FIELD  = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        db_table = 'auth_user'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.first_name} {self.last_name} <{self.email}>'

    def get_full_name(self):
        return f'{self.first_name} {self.last_name}'.strip()

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT


class StudentProfile(models.Model):
    class Category(models.TextChoices):
        GEN  = 'GEN',  'General'
        OBC  = 'OBC',  'OBC'
        SC   = 'SC',   'SC'
        ST   = 'ST',   'ST'
        EWS  = 'EWS',  'EWS'

    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    phone             = models.CharField(max_length=15, blank=True)
    category          = models.CharField(max_length=10, choices=Category.choices, default=Category.GEN)
    state_of_domicile = models.CharField(max_length=60, blank=True)
    neet_year         = models.PositiveSmallIntegerField(null=True, blank=True)
    neet_score        = models.PositiveSmallIntegerField(null=True, blank=True)
    neet_rank         = models.PositiveIntegerField(null=True, blank=True)
    created_at        = models.DateTimeField(auto_now_add=True)
    updated_at        = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'student_profiles'

    def __str__(self):
        return f'{self.user.get_full_name()} | Rank: {self.neet_rank or "N/A"}'
