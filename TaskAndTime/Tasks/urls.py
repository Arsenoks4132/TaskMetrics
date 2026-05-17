from django.urls import path
from django.contrib.auth.views import LogoutView

from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [
    path('', views.HomePage.as_view(), name='home'),
    path('login/employee', views.LoginEmployee.as_view(), name='login_employee'),
    path('login/supervisor', views.LoginSupervisor.as_view(), name='login_supervisor'),
    path('registration', views.RegisterUser.as_view(), name='registration'),
    path('profile', cache_page(10)(views.ProfileUser.as_view()), name='profile'),
    path('profile/edit', views.EditProfile.as_view(), name='edit_profile'),
    path('profile/password', views.ChangePassword.as_view(), name='change_password'),
    path('logout', LogoutView.as_view(), name='logout'),
    path('statistics', cache_page(30)(views.Statistics.as_view()), name='statistics'),
    path('categories', views.CategoryList.as_view(), name='categories'),
    path('categories/new', views.CreateCategory.as_view(), name='create_category'),
    path('categories/edit/<int:category_id>', views.EditCategory.as_view(), name='edit_category'),
    path('categories/delete/<int:category_id>', views.DeleteCategory.as_view(), name='delete_category'),
    path('tasks/<int:employee_id>', cache_page(20)(views.TasksList.as_view()), name='tasks_list'),
    path('tasks/edit/<int:task_id>', views.EditTask.as_view(), name='edit_task'),
    path('tasks/delete/<int:task_id>', views.DeleteTask.as_view(), name='delete_task'),
]