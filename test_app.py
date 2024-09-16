import unittest
from flask import session
from app import app, get_db_connection, create_users_table

class FlaskAppTestCase(unittest.TestCase):


    @classmethod
    def setUpClass(cls):
        # Set up the application context and initialize the database for testing
        app.config['TESTING'] = True
        app.config['DATABASE'] = ':memory:'  # Use an in-memory database for testing
        cls.client = app.test_client()  # Create a test client
        with app.app_context():
            create_users_table()  # Create the users table for testing

    def setUp(self):
        # Set up the application context for each test
        self.ctx = app.app_context()
        self.ctx.push()  # Push the application context
        self.conn = get_db_connection()

    def tearDown(self):
        # Tear down the application context after each test
        self.conn.close()
        self.ctx.pop()  # Pop the application context

    def test_home_page(self):
        # Test that the home page loads correctly
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"University of Warwick's recreational and sports facilities", response.data)

    def test_registration(self):
        # Test the registration process
        response = self.client.post('/register', data={
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Registration successful, please log in.', response.data)

    def test_duplicate_registration(self):
        # Test duplicate registration
        self.client.post('/register', data={
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        response = self.client.post('/register', data={
            'email': 'testuser@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertIn(b'This email is already registered, please use another email.', response.data)

    def test_login(self):
        # Register a user first
        self.client.post('/register', data={
            'email': 'testlogin@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)

        # Test login
        response = self.client.post('/login', data={
            'username': 'testlogin@example.com',
            'password': 'testpassword'
        }, follow_redirects=True)
        self.assertIn(b'Login successful.', response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['username'], 'testlogin@example.com')

    def test_failed_login(self):
        # Test login with incorrect credentials
        response = self.client.post('/login', data={
            'username': 'wronguser@example.com',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        self.assertIn(b'Incorrect username or password, please try again.', response.data)

    def test_logout(self):
        # Test the logout functionality
        with self.client:
            self.client.post('/register', data={
                'email': 'logoutuser@example.com',
                'password': 'logoutpassword'
            }, follow_redirects=True)
            self.client.post('/login', data={
                'username': 'logoutuser@example.com',
                'password': 'logoutpassword'
            }, follow_redirects=True)
            response = self.client.get('/logout', follow_redirects=True)
            self.assertIn(b'You have successfully logged out.', response.data)
            self.assertNotIn('username', session)

    def test_add_to_cart(self):
        # Test adding an item to the cart
        with self.client.session_transaction() as sess:
            sess['cart'] = []  # Ensure cart is empty initially
        response = self.client.post('/add_to_cart', data={
            'product_name': 'Membership - Monthly',
            'product_price': '30'
        }, follow_redirects=True)
        self.assertIn(b'Membership - Monthly has been added to the cart!', response.data)

    def test_clear_cart(self):
        # Test clearing the cart
        with self.client.session_transaction() as sess:
            sess['cart'] = [{'name': 'Membership - Monthly', 'price': '30'}]
        response = self.client.get('/clear_cart', follow_redirects=True)
        self.assertIn(b'Your cart has been cleared.', response.data)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess.get('cart'), None)

if __name__ == '__main__':
    unittest.main()