document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.getElementById('loginForm');
    const emailInput = loginForm.querySelector('input[name="email"]');
    const passwordInput = loginForm.querySelector('input[name="password"]');
    const emailError = document.getElementById('emailError');
    const passwordError = document.getElementById('passwordError');
    const formError = document.getElementById('formError');

    loginForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        emailError.textContent = '';
        passwordError.textContent = '';
        formError.textContent = '';

        const email = emailInput.value.trim();
        const password = passwordInput.value.trim();

        if (!email) {
            emailError.textContent = 'Email is required.';
            return;
        }
        if (!password) {
            passwordError.textContent = 'Password is required.';
            return;
        }

        try {
            const response = await fetch('/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
            });
            const result = await response.json();
            if (response.ok && result.success) {
                // Redirect to dashboard
                window.location.href = '/dashboard';
            } else {
                formError.textContent = result.message || 'Login failed.';
            }
        } catch (error) {
            formError.textContent = 'An error occurred. Please try again later.';
            console.error('Login error:', error);
        }
    });
});
