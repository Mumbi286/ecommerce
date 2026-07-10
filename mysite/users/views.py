from django.shortcuts import render,redirect
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode
from django.http import HttpResponse
from .forms import CreateUserForm
from django.utils.encoding import force_bytes,force_str
from django.template.loader import render_to_string
from django.contrib.auth.models import User
from .token import account_activation_token
from .forms import LoginForm
from .forms import UserUpdateForm
from django.contrib.auth import authenticate,login,logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme


# Create your views here.
def register(request):
    form = CreateUserForm()
    if request.method == "POST":
        form = CreateUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.is_active = False
            user.save()
            current_site= get_current_site(request)


            # Email verification logic
            subject = 'Verify your email to activate your accoount'
            message = render_to_string('users/email-verification.html',{
                'user':user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            # sending the email to the user
            user.email_user(subject=subject,message=message)
            return redirect('email-verification-sent')





        
    return render(request,'users/register.html',{'form':form})

def email_verification(request,uidb64,token):
    unique_id = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=unique_id)
    # checking if the user exists
    if user and account_activation_token.check_token(user,token):
        user.is_active=True
        user.save()
        return redirect('email-verification-success')
    else:
        return redirect('email-verification-failed')


def email_verification_sent(request):
    return render(request,'users/email-verification-sent.html')


def email_verification_success(request):
    return render(request,'users/email-verification-success.html')
    

def email_verification_failed(request):
    return render(request,'users/email-verification-failed.html')


def user_login(request):
    form = LoginForm()
    # checking if the user is valid and not
    if request.method =="POST":
        form = LoginForm(request,data=request.POST)
        if form.is_valid():
            username= request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(request,username=username,password=password)
            if user is not None:
                login(request,user)
                # if login_required sent the user here, take them back to
                # the page they wanted; only allow paths on our own site
                next_url = request.POST.get('next') or request.GET.get('next')
                if next_url and url_has_allowed_host_and_scheme(next_url,allowed_hosts={request.get_host()}):
                    return redirect(next_url)
                return redirect('index')
            

    return render(request,'users/login.html',{'form':form})

def user_logout(request):
    logout(request)
    return redirect('index')

@login_required
def profile(request):

    if request.method=="POST":
        user_form = UserUpdateForm(request.POST,instance=request.user)
        if user_form.is_valid():
            user_form.save()
            return redirect('index')
    user_form = UserUpdateForm(instance=request.user)
        

    return render(request,'users/profile.html',{'user_form':user_form})

