import unittest
from unittest.mock import patch

import app.auth as auth


class SessionState(dict):
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


class FakeStreamlit:
    def __init__(self):
        self.session_state = SessionState()
        self._button_value = False
        self.rerun_called = False

    def button(self, *args, **kwargs):
        return self._button_value

    def rerun(self):
        self.rerun_called = True


class TestSessionCleanup(unittest.TestCase):
    def test_logout_clears_all_transient_state(self):
        fake = FakeStreamlit()
        fake.session_state.update(
            {
                "authenticated": True,
                "user": {"username": "admin"},
                "last_response": object(),
                "last_question": "consulta previa",
                "question_input": "consulta previa",
                "example_selector": "ejemplo",
                "feedback_saved": True,
                "feedback_choice": "Correcta / útil",
                "feedback_comment": "comentario",
                "query_history": ["q1", "q2"],
            }
        )
        fake._button_value = True

        with patch.object(auth, "st", fake):
            auth.logout_button()

        self.assertEqual(dict(fake.session_state), {})
        self.assertTrue(fake.rerun_called)

    def test_logout_without_click_keeps_state(self):
        fake = FakeStreamlit()
        fake.session_state.update(
            {
                "authenticated": True,
                "user": {"username": "admin"},
                "last_question": "consulta",
            }
        )
        fake._button_value = False

        with patch.object(auth, "st", fake):
            auth.logout_button()

        self.assertIn("authenticated", fake.session_state)
        self.assertIn("last_question", fake.session_state)
        self.assertFalse(fake.rerun_called)

    def test_init_auth_state_recreates_clean_auth_keys(self):
        fake = FakeStreamlit()

        with patch.object(auth, "st", fake):
            auth.init_auth_state()

        self.assertFalse(fake.session_state.authenticated)
        self.assertIsNone(fake.session_state.user)

    def test_logout_only_operates_on_session_state(self):
        fake = FakeStreamlit()
        fake.session_state.update(
            {
                "authenticated": True,
                "last_question": "consulta",
            }
        )
        fake._button_value = True

        with patch.object(auth, "st", fake):
            auth.logout_button()

        self.assertEqual(dict(fake.session_state), {})


if __name__ == "__main__":
    unittest.main()
