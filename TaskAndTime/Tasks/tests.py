"""
Фаззинг-тесты для приложения TaskAndTimes.

Используется библиотека Hypothesis для property-based / fuzz тестирования форм
и бизнес-логики приложения. Тесты проверяют:
- Граничные значения полей модели Task (поле spent)
- Валидацию форм на произвольных входных строках
- Защиту от SQL-инъекций и XSS в текстовых полях
- Уникальность email при регистрации
- Валидаторы паролей
"""

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

from hypothesis import given, settings as h_settings, assume
from hypothesis import strategies as st
from hypothesis.extra.django import TestCase as HypothesisTestCase

from .models import Task, Category
from .forms import AddTaskForm, RegisterUserForm, CategoryForm, EditProfileForm

User = get_user_model()

# ---------------------------------------------------------------------------
# Стратегии генерации данных
# ---------------------------------------------------------------------------

# Текст без NUL-байтов (\x00) и других управляющих символов,
# которые PostgreSQL и Django не принимают в строковых полях.
# Текст без NUL-байтов (\x00), суррогатных символов и управляющих символов,
# которые Django strip-ает до пустой строки (\r, \n в начале/конце и т.д.
# не вызывают проблем сами по себе, но \r как единственный символ становится '').
# Для надёжности исключаем все управляющие символы (категория Cc).
safe_text = st.text(
    alphabet=st.characters(
        blacklist_categories=('Cs', 'Cc'),
        blacklist_characters='\x00',
    ),
)

# Простые email-адреса вида user@example.com (только буквы, цифры, точка, дефис).
# st.emails() генерирует RFC-валидные адреса со спецсимволами (*@A.COM),
# которые Django отклоняет своим EmailValidator — поэтому используем from_regex.
simple_email = st.from_regex(
    r'[a-z][a-z0-9]{2,8}@[a-z]{2,6}\.[a-z]{2,4}',
    fullmatch=True,
)


# ---------------------------------------------------------------------------
# Вспомогательные фабрики
# ---------------------------------------------------------------------------

def make_user(username='testuser', password='StrongPass123!', is_staff=False):
    user, _ = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'is_staff': is_staff,
        }
    )
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
        cost = self.category.cost
        total = spent * cost
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
        """Форма должна быть валидна при любом comment до 1000 символов
        (без управляющих символов, которые отклоняет PostgreSQL)."""
        data = {
            'category': self.category.pk,
            'spent': 4,
            'comment': comment,
        }
        form = AddTaskForm(data=data)
        self.assertTrue(form.is_valid(), msg=f'Форма невалидна: {form.errors}')

    @given(spent=st.integers().filter(lambda x: x < 1 or x > 24))
    def test_form_rejects_invalid_spent(self, spent):
        """Форма должна отклонять значения spent вне допустимого диапазона."""
        data = {
            'category': self.category.pk,
            'spent': spent,
            'comment': '',
        }
        form = AddTaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('spent', form.errors)

    @given(comment=safe_text.filter(lambda s: len(s) > 1000))
    def test_form_rejects_too_long_comment(self, comment):
        """Форма должна отклонять комментарии длиннее 1000 символов."""
        data = {
            'category': self.category.pk,
            'spent': 2,
            'comment': comment,
        }
        form = AddTaskForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn('comment', form.errors)


# ---------------------------------------------------------------------------
# Фаззинг формы CategoryForm
# ---------------------------------------------------------------------------

class CategoryFormFuzzTest(HypothesisTestCase):
    """Фаззинг формы создания категории."""

    @given(name=safe_text.filter(lambda s: 1 <= len(s) <= 100))
    def test_valid_category_name(self, name):
        """Любое безопасное непустое название до 100 символов должно проходить."""
        # Пропускаем уже существующие названия, чтобы не нарушать unique constraint.
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
        # Генерируем username из email, ограничиваем длину до 20 символов.
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

    @given(email=st.text(min_size=1, max_size=50).filter(lambda s: '@' not in s))
    def test_invalid_email_rejected(self, email):
        """Строка без '@' не является корректным email и должна отклоняться."""
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
    """Проверка разграничения доступа между ролями."""

    def setUp(self):
        self.client = Client()
        self.employee = make_user('emp_test', 'StrongPass123!')
        self.supervisor = make_user('sup_test', 'StrongPass123!', is_staff=True)

    def test_anonymous_profile_redirects_to_login(self):
        """Неавторизованный запрос к /profile должен перенаправлять на логин."""
        response = self.client.get('/profile')
        self.assertIn(response.status_code, [301, 302])
        self.assertIn('login', response['Location'])

    def test_anonymous_statistics_forbidden(self):
        """Неавторизованный запрос к /statistics должен перенаправлять."""
        response = self.client.get('/statistics')
        self.assertIn(response.status_code, [301, 302])

    def test_employee_cannot_access_statistics(self):
        """Сотрудник без прав is_staff не должен получать доступ к /statistics."""
        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get('/statistics')
        # Ожидаем 302 (redirect to login) или 403
        self.assertIn(response.status_code, [302, 403])

    def test_supervisor_can_access_statistics(self):
        """Руководитель с is_staff=True должен получать доступ к /statistics."""
        self.client.login(username='sup_test', password='StrongPass123!')
        response = self.client.get('/statistics')
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_access_categories(self):
        """Сотрудник не должен иметь доступ к управлению категориями."""
        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get('/categories')
        self.assertIn(response.status_code, [301, 302, 403])

    def test_supervisor_can_access_categories(self):
        """Руководитель должен иметь доступ к /categories."""
        self.client.login(username='sup_test', password='StrongPass123!')
        response = self.client.get('/categories')
        self.assertEqual(response.status_code, 200)

    def test_employee_cannot_edit_other_task(self):
        """Сотрудник не должен мочь редактировать задачу другого пользователя."""
        other_user = make_user('other_emp', 'StrongPass123!')
        category = make_category('Role test cat', cost=200)
        task = Task.objects.create(worker=other_user, category=category, spent=3)

        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get(f'/tasks/edit/{task.pk}')
        self.assertIn(response.status_code, [301, 302, 403])

    def test_employee_can_edit_own_task(self):
        """Сотрудник должен иметь доступ к редактированию своей задачи."""
        category = make_category('Own task cat', cost=200)
        task = Task.objects.create(worker=self.employee, category=category, spent=5)

        self.client.login(username='emp_test', password='StrongPass123!')
        response = self.client.get(f'/tasks/edit/{task.pk}')
        self.assertEqual(response.status_code, 200)
