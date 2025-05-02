document.addEventListener('DOMContentLoaded', () => {
    // Общие функции
    const apiUrl = 'http://localhost:8000';

    // Обработка форм
    const handleFormSubmit = async (formId, endpoint, successMessage, redirectPage) => {
        const form = document.getElementById(formId);
        if (!form) return;

        form.onsubmit = async (e) => {
            e.preventDefault();
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            try {
                const response = await fetch(`${apiUrl}/${endpoint}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password
                    })
                });

                const data = await response.json();
                if (!response.ok) throw new Error(data.detail || 'Something went wrong');

                alert(successMessage);
                if (redirectPage) window.location.href = redirectPage;
            } catch (error) {
                alert(error.message);
            }
        };
    };

    // Инициализация форм
    handleFormSubmit('loginForm', 'login', 'Login successful!', 'users.html');
    handleFormSubmit('registerForm', 'register', 'Registration successful!', 'index.html');

    // Загрузка пользователей
    const loadUsers = async () => {
        try {
            const response = await fetch(`${apiUrl}/users`);
            const users = await response.json();

            const usersList = document.getElementById('usersList');
            if (usersList) {
                usersList.innerHTML = users.map(user => `
                    <div class="user-item">
                        <strong>ID:</strong> ${user.id}<br>
                        <strong>Username:</strong> ${user.username}
                    </div>
                `).join('');
            }
        } catch (error) {
            console.error('Error loading users:', error);
        }
    };

    loadUsers();
});