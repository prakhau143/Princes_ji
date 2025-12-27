from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import random
import string
from .models import PasswordResetOTP
from datetime import datetime, timedelta
from django.utils import timezone

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Check if user is admin/staff and redirect accordingly
            if user.is_staff or user.is_superuser:
                return redirect('admin-dashboard')
            else:
                return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'auth/login.html')

def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        mobile = request.POST.get('mobile')
        password = request.POST.get('password1')
        confirm_password = request.POST.get('password2')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'auth/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'auth/register.html')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        
        # Create user profile with mobile number
        from .models import UserProfile
        UserProfile.objects.create(user=user, mobile=mobile)
        
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('login')
    
    return render(request, 'auth/register.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        try:
            user = User.objects.get(email=email)
            
            # Generate 6-digit OTP
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Delete any existing OTPs for this user
            PasswordResetOTP.objects.filter(user=user).delete()
            
            # Create new OTP
            PasswordResetOTP.objects.create(user=user, otp=otp)
            
            # Send email
            subject = 'Password Reset OTP - Princess Jewelry'
            message = f'''
Hello {user.username},

You have requested to reset your password for Princess Jewelry.

Your OTP is: {otp}

This OTP is valid for 10 minutes. Please use it to reset your password.

If you didn't request this, please ignore this email.

Best regards,
Princess Jewelry Team
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            request.session['reset_email'] = email
            messages.success(request, 'OTP sent to your email address.')
            return redirect('verify_otp')
            
        except User.DoesNotExist:
            messages.error(request, 'No account found with this email address.')
    
    return render(request, 'auth/forgot_password.html')

def verify_otp_view(request):
    if 'reset_email' not in request.session:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        otp = request.POST.get('otp')
        email = request.session.get('reset_email')
        
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.get(
                user=user, 
                otp=otp, 
                is_used=False,
                created_at__gte=timezone.now() - timedelta(minutes=10)
            )
            
            request.session['verified_user_id'] = user.id
            messages.success(request, 'OTP verified successfully. Please set your new password.')
            return redirect('reset_password')
            
        except PasswordResetOTP.DoesNotExist:
            messages.error(request, 'Invalid or expired OTP.')
    
    return render(request, 'auth/verify_otp.html')

def reset_password_view(request):
    if 'verified_user_id' not in request.session:
        return redirect('forgot_password')
    
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'auth/reset_password.html')
        
        user_id = request.session.get('verified_user_id')
        user = User.objects.get(id=user_id)
        user.set_password(password)
        user.save()
        
        # Mark OTP as used
        PasswordResetOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Clear session
        del request.session['reset_email']
        del request.session['verified_user_id']
        
        messages.success(request, 'Password reset successfully! Please log in with your new password.')
        return redirect('login')
    
    return render(request, 'auth/reset_password.html')

@csrf_exempt
def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('reset_email')
        if not email:
            return JsonResponse({'success': False, 'message': 'Session expired'})
        
        try:
            user = User.objects.get(email=email)
            
            # Generate new OTP
            otp = ''.join(random.choices(string.digits, k=6))
            
            # Delete old OTPs
            PasswordResetOTP.objects.filter(user=user).delete()
            
            # Create new OTP
            PasswordResetOTP.objects.create(user=user, otp=otp)
            
            # Send email
            subject = 'Password Reset OTP - Princess Jewelry'
            message = f'''
Hello {user.username},

Your new OTP is: {otp}

This OTP is valid for 10 minutes.

Best regards,
Princess Jewelry Team
            '''
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [email],
                fail_silently=False,
            )
            
            return JsonResponse({'success': True, 'message': 'New OTP sent successfully'})
            
        except User.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'User not found'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request'})
