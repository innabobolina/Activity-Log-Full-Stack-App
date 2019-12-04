from unittest import TestCase, main
from server import app


class FlaskTests(TestCase):

  def setUp(self):
      """Setup before every test."""

      self.client = app.test_client()
      app.config['TESTING'] = True

  def test_homepage(self):
      """Test the homepage route."""

      result = self.client.get("/")
      self.assertEqual(result.status_code, 200)
      self.assertIn(b'<h2>Welcome to Activity Log!</h2>', result.data)


  # def test_login(self):
  #       """Test login page."""

  #       result = self.client.post("/login",
  #                                 data={"user_id": "rachel", "password": "123"},
  #                                 follow_redirects=True)
  #       self.assertIn(b"You are a valued user", result.data)


# class FlaskTestsLoggedIn(TestCase):
#     """Flask tests with user logged in to session."""

#     def setUp(self):
#         """Stuff to do before every test."""

#         app.config['TESTING'] = True
#         app.config['SECRET_KEY'] = 'key'
#         self.client = app.test_client()

#         with self.client as c:
#             with c.session_transaction() as sess:
#                 sess['user_id'] = 1

#     def test_important_page(self):
#         """Test important page."""

#         result = self.client.get("/important")
#         self.assertIn(b"You are a valued user", result.data)


# def setUp(self):
#     """Stuff to do before every test."""

#     # Get the Flask test client
#     self.client = app.test_client()
#     app.config['TESTING'] = True

#     # Connect to test database
#     connect_to_db(app, "postgresql:///testdb")

#     # Create tables and add sample data
#     db.create_all()
#     example_data()

# create sample data

if __name__ == '__main__':
    # If called like a script, run our tests
    main()