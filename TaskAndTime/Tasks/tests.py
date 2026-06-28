"""
Фаззинг-тесты для приложения TaskAndTimes.

Используется библиотека Hypothesis для property-based / fuzz тестирования форм
и бизнес-логики приложения. Тесты проверяют:
- Граничные значения полей модели Task (поле spent)
- Валидацию форм на произвольных входных строках (без управляющих символов)
- Валидацию форм на слишком длинные строки
- Уникальность email при регистрации
- Базовую защиту ролевой модели (анонимный доступ)
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

from hypothesis import given, assume
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from .models import Task, Category
from .forms import AddTaskForm, RegisterUserForm, CategoryForm

User = get_user_model()

# ---------------------------------------------------------------------------
# Стратегии генерации данных
# ---------------------------------------------------------------------------

# Текст без NUL-байтов и управляющих символов (Cc = control chars, Cs = surrogates).
# Django strip-ает \r до пустой строки и отклоняет \x00 в PostgreSQL-запросах.
safe_text = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters='\x00',
    ),
)

# Простые email-адреса вида user@example.com.
# st.emails() генерирует RFC-валидные адреса со спецсимволами (*@A.COM),
# которые Django отклоняет своим EmailValidator.
simple_email = st.from_regex(
    r'[a-z][a-z0-9]{2,8}@[a-z]{2,6}\.[a-z]{2,4}',
    fullmatch=True,
)


# ---------------------------------------------------------------------------
# Вспомогательные фабрики
# ---------------------------------------------------------------------------

def make_user(username='testuser', password='StrongPass123!', is_staff=False):
    """Создать или обновить пользователя с заданными параметрами."""
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': is_staff,
        }
    )
    if not created:
        user.is_staff = is_staff
        user.save(update_fields=['is_staff'])
    user.set_password(password)
    user.save()
    return user


def make_category(name='Разработка', cost=800):
    category, _ = Category.objects.get_or_create(name=name, defaults={'cost': cost})
    return category


# ---------------------------------------------------------------------------
# Тесты модели Task: поле spent (1..24)
# ---------------------------------------------------------------------------

class TaskModelValidationTest(HypothesisTestCase):
    """Фаззинг граничных значений поля Task.spent."""

    def setUp(self):
        self.user = make_user('fuzz_task_user')
        self.category = make_category('Фаззинг категория', cost=500)

    @given(spent=st.integers(min_value=1, max_value=24))
    def test_valid_spent_values(self, spent):
        """Любое значение spent в диапазоне [1, 24] должно проходить валидацию."""
        task = Task(worker=self.user, category=self.category, spent=spent)
        try:
            task.full_clean()
        except ValidationError as e:
            self.fail(f'Неожиданная ошибка валидации для spent={spent}: {e}')

    @given(spent=st.integers().filter(lambda x: x < 1 or x > 24))
    def test_invalid_spent_values(self, spent):
        """Значения spent вне диапазона [1, 24] должны вызывать ValidationError."""
        task = Task(worker=self.user, category=self.category, spent=spent)
        with self.assertRaises(ValidationError):
            task.full_clean()

    @given(spent=st.integers(min_value=1, max_value=24))
    def test_task_total_cost_calculation(self, spent):
        """Стоимость задачи (spent * cost) должна быть корректным целым числом."""
        total = spent * self.category.cost
        self.assertIsInstance(total, int)
        self.assertGreaterEqual(total, 0)


# ---------------------------------------------------------------------------
# Фаззинг формы AddTaskForm
# ---------------------------------------------------------------------------

class AddTaskFormFuzzTest(HypothesisTestCase):
    """Фаззинг формы добавления задачи."""

    def setUp(self):
        self.category = make_category('Form фаззинг', cost=300)

    @given(comment=safe_text.filter(lambda s: len(s) <= 1000))
    def test_form_accepts_any_valid_comment(self, comment):
        """Форма должна быть валидна при любом безопасном comment до 1000 символов."""
        data = {'category': self.category.pk, 'spent': 4, 'comment': comment}
        form = AddTaskForm(data=data)
        self.assertTrue(form.is_valid(), msg=f'Форма невалидна: {form.errors}')

    @given(spent=st.integers().filter(lambda x: x < 1 or x > 24))
    def test_form_rejects_invalid_spent(self, spent):
        """Форма должна отклонять значения spent вне допустимого диапазона."""
        data = {'category': self.category.pk, 'spent': spent, 'comment': ''}
        form = AddTaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('spent', form.errors)

    @given(comment=safe_text.filter(lambda s: len(s) > 1000))
    def test_form_rejects_too_long_comment(self, comment):
        """Форма должна отклонять комментарии длиннее 1000 символов."""
        data = {'category': self.category.pk, 'spent': 2, 'comment': comment}
        form = AddTaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)


# ---------------------------------------------------------------------------
# Фаззинг формы CategoryForm
# ---------------------------------------------------------------------------

class CategoryFormFuzzTest(HypothesisTestCase):
    """Фаззинг формы создания категории."""

    @given(name=safe_text.filter(lambda s: 1 <= len(s.strip()) <= 100))
    def test_valid_category_name(self, name):
        """Любое безопасное непустое (после strip) название до 100 символов должно проходить."""
        assume(not Category.objects.filter(name=name).exists())
        data = {'name': name, 'cost': 100}
        form = CategoryForm(data=data)
        self.assertTrue(form.is_valid(), msg=f'Форма невалидна для name={repr(name)}: {form.errors}')

    @given(cost=st.integers(min_value=0, max_value=1_000_000))
    def test_valid_category_cost(self, cost):
        """Стоимость категории должна принимать любое неотрицательное целое значение."""
        name = f'Cat_{cost}'
        assume(not Category.objects.filter(name=name).exists())
        data = {'name': name, 'cost': cost}
        form = CategoryForm(data=data)
        self.assertTrue(form.is_valid(), msg=f'Форма невалидна для cost={cost}: {form.errors}')

    @given(name=safe_text.filter(lambda s: len(s) > 100))
    def test_category_name_too_long(self, name):
        """Название категории длиннее 100 символов должно отклоняться."""
        data = {'name': name, 'cost': 500}
        form = CategoryForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('name', form.errors)


# ---------------------------------------------------------------------------
# Фаззинг формы RegisterUserForm: валидация email
# ---------------------------------------------------------------------------

class RegisterFormEmailFuzzTest(HypothesisTestCase):
    """Фаззинг поля email в форме регистрации."""

    @given(email=simple_email)
    def test_unique_email_accepted(self, email):
        """Уникальный корректный email должен проходить валидацию формы регистрации."""
        assume(not User.objects.filter(email=email).exists())
        username = f'u_{email.split("@")[0]}'[:20]
        assume(not User.objects.filter(username=username).exists())
        data = {
            'username': username,
            'email': email,
            'first_name': 'Test',
            'last_name': 'User',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        }
        form = RegisterUserForm(data=data)
        self.assertTrue(form.is_valid(), msg=f'Форма невалидна для email={email}: {form.errors}')

    @given(
        email=st.text(min_size=1, max_size=50).filter(
            lambda s: '@' not in s and s.strip() != ''
        )
    )
    def test_invalid_email_rejected(self, email):
        """Непустая строка без '@' не является корректным email и должна отклоняться."""
        data = {
            'username': 'someuser123',
            'email': email,
            'first_name': 'A',
            'last_name': 'B',
            'password1': 'StrongPass999!',
            'password2': 'StrongPass999!',
        }
        form = RegisterUserForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


# ---------------------------------------------------------------------------
# Тесты ролевой модели: проверка доступа к защищённым URL
# ---------------------------------------------------------------------------

class RoleBasedAccessTest(TestCase):
    """Проверка разграничения доступа между ролями.

    Тесты проверяют корректность разграничения доступа: анонимный пользователь
    перенаправляется на страницу входа, а попытки редактирования чужих данных
    проверяются на уровне модели через PermissionDenied.
    """

    def setUp(self):
        self.client = Client()
        self.employee = make_user('emp_test', 'StrongPass123!', is_staff=False)
        self.supervisor = make_user('sup_test', 'StrongPass123!', is_staff=True)
        content_type = ContentType.objects.get_for_model(User)
        view_user_perm = Permission.objects.get(codename='view_user', content_type=content_type)
        self.supervisor.user_permissions.add(view_user_perm)

    def tearDown(self):
        self.client.logout()

    def test_anonymous_profile_redirects_to_login(self):
        """Неаутентифицированный запрос к /profile перенаправляет на страницу входа."""
        response = self.client.get('/profile')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('login', response['Location'])

    def test_employee_can_access_own_profile(self):
        """Аутентифицированный сотрудник получает доступ к своему профилю."""
        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get('/profile')
        self.assertEqual(response.status_code, 200)

    def test_permission_denied_for_other_task(self):
        """PermissionDenied выбрасывается на уровне view при доступе к чужой задаче.

        Проверяем напрямую через view-логику, не через HTTP-клиент,
        чтобы исключить влияние кеша и middleware.
        """
        from django.core.exceptions import PermissionDenied
        from Tasks.views import EditTask
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.backends.db import SessionStore

        other_user = make_user('other_emp_perm', 'StrongPass123!')
        category = make_category('Perm test cat', cost=200)
        task = Task.objects.create(worker=other_user, category=category, spent=3)

        factory = RequestFactory()
        request = factory.get(f'/tasks/edit/{task.pk}')
        request.user = self.employee
        request.session = SessionStore()
        request.session.create()
        request._messages = FallbackStorage(request)

        view = EditTask()
        view.request = request
        view.kwargs = {'task_id': task.pk}

        with self.assertRaises(PermissionDenied):
            view.get_object()

    def test_no_permission_denied_for_own_task(self):
        """PermissionDenied не выбрасывается при доступе к своей задаче."""
        from Tasks.views import EditTask
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.backends.db import SessionStore

        category = make_category('Own perm cat', cost=200)
        task = Task.objects.create(worker=self.employee, category=category, spent=5)

        factory = RequestFactory()
        request = factory.get(f'/tasks/edit/{task.pk}')
        request.user = self.employee
        request.session = SessionStore()
        request.session.create()
        request._messages = FallbackStorage(request)

        view = EditTask()
        view.request = request
        view.kwargs = {'task_id': task.pk}

        # Не должно выбрасываться исключение
        obj = view.get_object()
        self.assertEqual(obj.pk, task.pk)

    def test_anonymous_statistics_forbidden(self):
        """Неаутентифицированный запрос к /statistics перенаправляется на страницу входа."""
        response = self.client.get('/statistics')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('login', response['Location'])

    def test_employee_cannot_access_statistics(self):
        """Сотрудник без прав доступа получает 403 при обращении к /statistics."""
        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get('/statistics')
        self.assertEqual(response.status_code, 403)

    def test_supervisor_can_access_statistics(self):
        """Руководитель с правом view_user получает HTTP 200 на /statistics."""
        self.client.login(username='sup_test', password='StrongPass123!')
        response = self.client.get('/statistics')
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_access_categories(self):
        """Сотрудник без прав доступа получает 403 при обращении к /categories."""
        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get('/categories')
        self.assertEqual(response.status_code, 403)

    def test_supervisor_can_access_categories(self):
        """Руководитель с правом view_user получает HTTP 200 на /categories."""
        self.client.login(username='sup_test', password='StrongPass123!')
        response = self.client.get('/categories')
        self.assertEqual(response.status_code, 200)

    def test_supervisor_can_edit_any_task(self):
        """Руководитель (is_staff=True) может получить любую задачу для редактирования."""
        from Tasks.views import EditTask
        from django.test import RequestFactory
        from django.contrib.messages.storage.fallback import FallbackStorage
        from django.contrib.sessions.backends.db import SessionStore

        other_user = make_user('other_emp_sup', 'StrongPass123!')
        category = make_category('Sup test cat', cost=200)
        task = Task.objects.create(worker=other_user, category=category, spent=3)

        factory = RequestFactory()
        request = factory.get(f'/tasks/edit/{task.pk}')
        request.user = self.supervisor
        request.session = SessionStore()
        request.session.create()
        request._messages = FallbackStorage(request)

        view = EditTask()
        view.request = request
        view.kwargs = {'task_id': task.pk}

        obj = view.get_object()
        self.assertEqual(obj.pk, task.pk)


# ---------------------------------------------------------------------------
# Фаззинг HTTP-эндпоинтов: обработка случайных параметров URL
# ---------------------------------------------------------------------------

class HttpEndpointFuzzTest(HypothesisTestCase):
    """Фаззинг HTTP-эндпоинтов приложения.

    Проверяет, что эндпоинты корректно обрабатывают случайные (в том числе
    несуществующие) идентификаторы в URL, не вызывая необработанных исключений
    (ошибка 500).
    """

    def setUp(self):
        self.client = Client()
        self.supervisor = make_user('fuzz_http_sup', 'StrongPass123!', is_staff=True)
        content_type = ContentType.objects.get_for_model(User)
        view_user_perm = Permission.objects.get(codename='view_user', content_type=content_type)
        self.supervisor.user_permissions.add(view_user_perm)

    @given(task_id=st.integers(min_value=1, max_value=10_000))
    def test_edit_task_fuzz_id_no_server_error(self, task_id):
        """Несуществующий task_id не должен вызывать 500."""
        self.client.login(username='fuzz_http_sup', password='StrongPass123!')
        response = self.client.get(f'/tasks/edit/{task_id}')
        self.assertNotEqual(response.status_code, 500)

    @given(task_id=st.integers(min_value=1, max_value=10_000))
    def test_delete_task_fuzz_id_no_server_error(self, task_id):
        """Несуществующий task_id на странице удаления не вызывает 500."""
        self.client.login(username='fuzz_http_sup', password='StrongPass123!')
        response = self.client.get(f'/tasks/delete/{task_id}')
        self.assertNotEqual(response.status_code, 500)

    @given(employee_id=st.integers(min_value=1, max_value=10_000))
    def test_tasks_list_fuzz_employee_no_server_error(self, employee_id):
        """Несуществующий employee_id в списке задач не вызывает 500."""
        self.client.login(username='fuzz_http_sup', password='StrongPass123!')
        response = self.client.get(f'/tasks/{employee_id}')
        self.assertNotEqual(response.status_code, 500)

    @given(category_id=st.integers(min_value=1, max_value=10_000))
    def test_edit_category_fuzz_id_no_server_error(self, category_id):
        """Несуществующий category_id при редактировании не вызывает 500."""
        self.client.login(username='fuzz_http_sup', password='StrongPass123!')
        response = self.client.get(f'/categories/edit/{category_id}')
        self.assertNotEqual(response.status_code, 500)

    @given(category_id=st.integers(min_value=1, max_value=10_000))
    def test_delete_category_fuzz_id_no_server_error(self, category_id):
        """Несуществующий category_id при удалении не вызывает 500."""
        self.client.login(username='fuzz_http_sup', password='StrongPass123!')
        response = self.client.get(f'/categories/delete/{category_id}')
        self.assertNotEqual(response.status_code, 500)
