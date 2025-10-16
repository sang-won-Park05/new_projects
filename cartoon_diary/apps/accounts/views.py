"""API views for account operations."""

from __future__ import annotations

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render
from django.views import View
from django import forms

from .serializers import LoginSerializer, SignupSerializer


class SignupView(generics.CreateAPIView):
    """Register a new user account."""

    serializer_class = SignupSerializer
    permission_classes = (permissions.AllowAny,)


class LoginView(APIView):
    """Authenticate a user and return a session placeholder."""

    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        # TODO: integrate JWT/session issuance
        return Response({"detail": "Login successful", "user_id": user.id}, status=status.HTTP_200_OK)


# ---- Site (HTML) views ----------------------------------------------------


class SiteSignupForm(forms.Form):
    email = forms.EmailField(label="이메일")
    username = forms.CharField(label="이름", required=False)
    password1 = forms.CharField(label="비밀번호", widget=forms.PasswordInput)
    password2 = forms.CharField(label="비밀번호 확인", widget=forms.PasswordInput)

    def clean(self):
        cleaned = super().clean()
        if cleaned.get("password1") != cleaned.get("password2"):
            raise forms.ValidationError("비밀번호가 일치하지 않습니다.")
        return cleaned


class SiteSignupView(View):
    template_name = "accounts/signup.html"

    def get(self, request):
        return render(request, self.template_name, {"form": SiteSignupForm()})

    def post(self, request):
        form = SiteSignupForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})

        serializer = SignupSerializer(
            data={
                "email": form.cleaned_data["email"],
                "username": form.cleaned_data.get("username"),
                "password": form.cleaned_data["password1"],
            }
        )
        if not serializer.is_valid():
            # Map DRF errors to Django form errors
            for field, errors in serializer.errors.items():
                if field == "non_field_errors":
                    for e in errors:
                        form.add_error(None, e)
                else:
                    for e in errors:
                        form.add_error(field, e)
            return render(request, self.template_name, {"form": form})

        user = serializer.save()

        # Auto-login then go to dashboard
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "회원가입이 완료되었습니다.")
        return redirect("/dashboard/")


class FindIdForm(forms.Form):
    name = forms.CharField(label="이름")
    email = forms.EmailField(label="이메일")


class FindIdView(View):
    template_name = "accounts/find_id.html"

    def get(self, request):
        return render(request, self.template_name, {"form": FindIdForm()})

    def post(self, request):
        form = FindIdForm(request.POST)
        if not form.is_valid():
            return render(request, self.template_name, {"form": form})
        # Our "ID" is the email itself; guide user accordingly.
        messages.info(request, "아이디는 가입하신 이메일 주소입니다: %s" % form.cleaned_data["email"]) 
        return redirect("login")
