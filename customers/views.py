from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import SignUpForm, SignInForm, ProfileEditForm
from orders.models import OnlineOrder, RetailTransaction

DELIVERY_GROUP_NAME = "delivery_agents"


def _is_delivery_agent(user) -> bool:
    if not user.is_authenticated:
        return False
    return user.groups.filter(name=DELIVERY_GROUP_NAME).exists()

def _theme_template(template_name: str) -> str:
    try:
        from core.models import ShopConfig
        base = ShopConfig.get().shop_template
    except Exception:
        base = "default"
    return f"themes/{base}/{template_name}"

def signup_view(request):
    if request.user.is_authenticated:
        if _is_delivery_agent(request.user):
            return redirect('delivery_orders')
        return redirect('product_list')

    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            customer = form.save()
            # Log them in immediately after signup
            login(request, customer.user)
            messages.success(request, "Account created successfully!")
            return redirect('product_list')
    else:
        form = SignUpForm()
        
    # We will need to create 'customers/signup.html'
    return render(request, _theme_template('customers/signup.html'), {'form': form})

def signin_view(request):
    if request.user.is_authenticated:
        if _is_delivery_agent(request.user):
            return redirect('delivery_orders')
        return redirect('product_list')

    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            phone = str(form.cleaned_data['phone'])
            password = form.cleaned_data['password']
            
            # Authenticate using the phone number (which is the username)
            user = authenticate(request, username=phone, password=password)
            if user is not None:
                if _is_delivery_agent(user):
                    messages.error(request, "Please sign in from the delivery console.")
                    return render(request, _theme_template('customers/signin.html'), {'form': form})
                if not hasattr(user, "customer"):
                    messages.error(request, "Customer account not found.")
                    return render(request, _theme_template('customers/signin.html'), {'form': form})
                login(request, user)
                messages.success(request, f"Welcome back!")
                # Redirect back to where they came from if 'next' is passed, else home
                next_page = request.GET.get('next', 'product_list')
                return redirect(next_page)
            else:
                messages.error(request, "Invalid phone number or password.")
    else:
        form = SignInForm()
        
    return render(request, _theme_template('customers/signin.html'), {'form': form})

def signout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('product_list')

@login_required
def profile_view(request):
    if _is_delivery_agent(request.user):
        messages.error(request, "Delivery agents cannot access customer profiles.")
        logout(request)
        return redirect('delivery_login')
    if not hasattr(request.user, "customer"):
        messages.error(request, "Customer profile not found.")
        return redirect('product_list')
    customer = request.user.customer
    
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = ProfileEditForm(instance=customer)
        
    online_orders = OnlineOrder.objects.filter(customer=customer).order_by('-created_at')
    retail_txns = RetailTransaction.objects.filter(customer=customer).order_by('-date')
    
    context = {
        'form': form,
        'online_orders': online_orders,
        'retail_txns': retail_txns,
    }
    return render(request, _theme_template('customers/profile.html'), context)
