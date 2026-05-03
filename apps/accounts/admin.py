from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as Base
from .models import User, StudentProfile

@admin.register(User)
class UserAdmin(Base):
    list_display  = ['email','first_name','last_name','role','is_active','date_joined']
    list_filter   = ['role','is_active']
    search_fields = ['email','first_name','last_name']
    ordering      = ['-date_joined']
    fieldsets = (
        (None, {'fields': ('email','password')}),
        ('Personal', {'fields': ('first_name','last_name')}),
        ('Role & Status', {'fields': ('role','is_active','is_staff','is_superuser','is_verified')}),
        ('Permissions', {'fields': ('groups','user_permissions')}),
    )
    add_fieldsets = ((None,{'classes':('wide',),'fields':('email','first_name','last_name','password1','password2')}),)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display  = ['user','category','state_of_domicile','neet_rank','neet_score']
    search_fields = ['user__email','user__first_name']
