import unittest
from unittest.mock import patch
from app import create_app, db
from app.models.user import User

class AuthTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_register_page_loads(self):
        response = self.client.get('/auth/register', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Sign Up', response.data)

    @patch('app.auth.routes.get_google_oauth')
    def test_google_login_and_registration(self, mock_get_oauth):
        # Setup mock OAuth client return token data
        mock_client = mock_get_oauth.return_value
        mock_client.authorize_access_token.return_value = {
            'userinfo': {
                'sub': '123456789',
                'email': 'alice@test.com',
                'name': 'Alice Student',
                'picture': 'http://avatar.url'
            }
        }
        
        # Trigger Google OAuth callback
        response = self.client.get('/auth/google/callback', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Alice Student', response.data or b'') # Check if logged in status displays name
        
        # Verify user is created in database
        user = User.query.filter_by(google_id='123456789').first()
        self.assertIsNotNone(user)
        self.assertEqual(user.name, "Alice Student")
        self.assertEqual(user.email, "alice@test.com")
        self.assertEqual(user.role, "student")
        self.assertEqual(user.avatar_url, 'http://avatar.url')

if __name__ == '__main__':
    unittest.main()
