from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import date, timedelta

from .models import Book, Borrow


# 🔒 Admin check
def is_admin(user):
    return user.is_staff


# ================= AUTH ================= #

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return render(request, 'signup.html', {'error': 'All fields required'})

        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists'})

        User.objects.create_user(username=username, password=password)
        return redirect('login')

    return render(request, 'signup.html')


from django.middleware.csrf import rotate_token

def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            rotate_token(request)   #

            if user.is_staff:
                return redirect('admin_dashboard')
            else:
                return redirect('dashboard')

        return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


@login_required
def user_logout(request):
    logout(request)
    return redirect('login')


# ================= USER DASHBOARD ================= #

@login_required
def dashboard(request):
    books = Book.objects.all()
    borrowed = Borrow.objects.filter(user=request.user, status='approved')
    history = Borrow.objects.filter(user=request.user)

    return render(request, 'dashboard.html', {
        'books': books,
        'borrowed': borrowed,
        'history': history
    })


# ================= BORROW ================= #

@login_required
def borrow_book(request, book_id):
    book = get_object_or_404(Book, id=book_id)

    # prevent duplicate request
    if Borrow.objects.filter(user=request.user, book=book, status='pending').exists():
        return redirect('dashboard')

    Borrow.objects.create(
        user=request.user,
        book=book,
        due_date=date.today() + timedelta(days=7),
        status='pending'
    )

    return redirect('dashboard')


# ================= ADMIN ================= #

@user_passes_test(is_admin, login_url='login')
def admin_dashboard(request):
    pending = Borrow.objects.filter(status='pending')
    approved = Borrow.objects.filter(status='approved')
    rejected = Borrow.objects.filter(status='rejected')

    return render(request, 'admin_dashboard.html', {
        'pending': pending,
        'approved': approved,
        'rejected': rejected
    })


@user_passes_test(is_admin, login_url='login')
def approve_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)

    # prevent double action
    if borrow.status != 'pending':
        return redirect('admin_dashboard')

    if borrow.book.available_copies > 0:
        borrow.status = 'approved'
        borrow.book.available_copies -= 1
        borrow.book.save()
    else:
        borrow.status = 'rejected'

    borrow.save()
    return redirect('admin_dashboard')


@user_passes_test(is_admin, login_url='login')
def reject_borrow(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.status != 'pending':
        return redirect('admin_dashboard')

    borrow.status = 'rejected'
    borrow.save()

    return redirect('admin_dashboard')


# ================= RETURN ================= #

@login_required
def return_book(request, borrow_id):
    borrow = get_object_or_404(Borrow, id=borrow_id)

    if borrow.status != 'approved':
        return redirect('dashboard')

    borrow.status = 'returned'
    borrow.return_date = date.today()

    days_late = (borrow.return_date - borrow.due_date).days
    fine = days_late * 10 if days_late > 0 else 0

    # ⚠️ make sure model has this field OR remove this line
    borrow.fine = fine

    borrow.save()

    book = borrow.book
    book.available_copies += 1
    book.save()

    return render(request, 'fine.html', {'fine': fine})