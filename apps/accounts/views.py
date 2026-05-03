"""apps/accounts/views.py — Web auth views"""
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib import messages
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

from .forms import LoginForm, RegisterForm

User = get_user_model()


class LoginView(View):
    template_name = 'registration/login.html'

    def get(self, request):
        if request.user.is_authenticated:
            return redirect('predictions:predict')
        return render(request, self.template_name, {'form': LoginForm()})

    def post(self, request):
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(request,
                                username=form.cleaned_data['email'],
                                password=form.cleaned_data['password'])
            if user:
                login(request, user)
                return redirect(request.GET.get('next', 'predictions:predict'))
            messages.error(request, 'Invalid email or password.')
        return render(request, self.template_name, {'form': form})


class RegisterView(View):
    template_name = 'registration/register.html'

    def get(self, request):
        return render(request, self.template_name, {'form': RegisterForm()})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            d    = form.cleaned_data
            user = User.objects.create_user(
                email      = d['email'],
                password   = d['password'],
                first_name = d['first_name'],
                last_name  = d['last_name'],
            )
            # Create student profile
            from .models import StudentProfile
            StudentProfile.objects.create(
                user              = user,
                category          = d['category'],
                state_of_domicile = d.get('state_of_domicile', ''),
                neet_rank         = d.get('neet_rank'),
                neet_score        = d.get('neet_score'),
            )
            login(request, user)
            messages.success(request, f'Welcome, {user.first_name}! Your account is ready.')
            return redirect('predictions:predict')
        return render(request, self.template_name, {'form': form})


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect('accounts-web:login')


@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    template_name = 'registration/profile.html'

    def get(self, request):
        profile, _ = request.user.student_profile.__class__.objects.get_or_create(user=request.user)
        return render(request, self.template_name, {'profile': profile})
