from django.contrib.auth.forms import UserCreationForm,AuthenticationForm
from django.contrib.auth.models import User
from django import forms



# creating user registation form  
class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username','email','password1','password2']

    def __init__(self, *args, **kwargs):
        super(CreateUserForm,self).__init__(*args,**kwargs)
        for fields in self.fields.values():
            fields.widget.attrs.update({
                'class':'w-full px-3 py-2 border border-gray-300 rounded'
            })


# Login form 
class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

# Profile form 
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username','email']
        exclude = ['password1','password2']

