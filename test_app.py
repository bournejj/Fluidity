from app import app
from unittest import TestCase

class SignInTestCase(TestCase):
    def test_sign_in(self):
        with app.test_client() as client:
            res = client.get('/')

            self.assertEqual(res.status_code, 200)
          

class HomeTestCase(TestCase):
    def test_home_Page(self):
        with app.test_client() as client:
            res = client.get('/home')

            self.assertEqual(res.status_code, 200)

            
        
            
            





