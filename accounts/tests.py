from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


class LoginTest(StaticLiveServerTestCase):
    """Selenium tests for login/logout functionality."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')
        cls.browser = webdriver.Chrome(
            service=ChromeService(ChromeDriverManager().install()),
            options=chrome_options,
        )
        cls.browser.implicitly_wait(5)

    @classmethod
    def tearDownClass(cls):
        cls.browser.quit()
        super().tearDownClass()

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            email='test@example.com',
        )

    # ---------- helpers ----------
    def _wait_for(self, by, value, timeout=10):
        return WebDriverWait(self.browser, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    # ---------- tests ----------
    def test_login_valid_then_logout(self):
        """
        Steps 1-7: Navigate to home, click Login, enter valid credentials,
        verify login, logout, verify logout.
        """
        # 1. Open home page
        self.browser.get(self.live_server_url + '/')
        self.assertIn('MySite', self.browser.title)

        # 2. Click the "Login" button in the top-right corner
        login_link = self._wait_for(By.ID, 'login-btn')
        login_link.click()

        # 3. Enter valid credentials
        username_input = self._wait_for(By.ID, 'username')
        password_input = self.browser.find_element(By.ID, 'password')
        username_input.send_keys('testuser')
        password_input.send_keys('testpass123')

        # 4. Click the "Login" button
        self.browser.find_element(By.ID, 'login-submit').click()

        # 5. Verify the user is logged in
        self._wait_for(By.ID, 'logout-btn')
        self.assertIn('Welcome, testuser', self.browser.page_source)
        self.assertIn('You are logged in', self.browser.page_source)

        # 6. Click "Logout"
        logout_btn = self.browser.find_element(By.ID, 'logout-btn')
        logout_btn.click()

        # 7. Verify the user is logged out
        self._wait_for(By.ID, 'login-btn')
        self.assertNotIn('Welcome, testuser', self.browser.page_source)
        self.assertIn('Welcome to MySite', self.browser.page_source)

    def test_login_invalid_credentials(self):
        """
        Steps 8-12: Enter invalid credentials and verify error message.
        """
        # Navigate to login page
        self.browser.get(self.live_server_url + '/login/')

        # 8-10. Enter invalid credentials
        username_input = self._wait_for(By.ID, 'username')
        password_input = self.browser.find_element(By.ID, 'password')
        username_input.send_keys('wronguser')
        password_input.send_keys('wrongpass')

        # 11. Click the "Login" button
        self.browser.find_element(By.ID, 'login-submit').click()

        # 12. Verify error message and user is NOT logged in
        error_msg = self._wait_for(By.CSS_SELECTOR, '.messages li.error')
        self.assertIn('Invalid username or password', error_msg.text)

        # Should still be on the login page, no logout button
        self.assertEqual(
            self.browser.current_url,
            self.live_server_url + '/login/',
        )
        # The login form should still be visible
        self.assertTrue(
            self.browser.find_element(By.ID, 'login-submit').is_displayed()
        )
