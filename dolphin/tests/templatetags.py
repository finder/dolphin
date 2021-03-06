import re

from django.contrib.auth.models import User
from django.template import Context, Template

from dolphin.middleware import LocalStoreMiddleware
from dolphin.tests.flipper import BaseTest

class ActiveTagTest(BaseTest):
    fixtures = ['dolphin_base_flags.json']

    def check_res(self, text, expected):
        t = Template(text)
        c = Context()

        res = t.render(c)
        res = ' '.join(re.findall("[a-zA-Z0-9]+", res)) #strip \n and spaces
        self.assertEqual(res,
                         expected)

    def test_ifactive_enabled(self):
        text = r"""
        {% load dolphin_tags %}
        {% ifactive "enabled" %}
        Test
        {% endifactive %}
        """

        expected_resp = "Test"
        self.check_res(text, expected_resp)

    def test_ifactive_disabled(self):
        text = r"""
        {% load dolphin_tags %}
        {% ifactive "testing_disabled" %}
        Test2
        {% else %}
        Test3
        {% endifactive %}
        """
        expected_resp = "Test3"
        self.check_res(text, expected_resp)

    def test_ifactive_missing(self):
        text = r"""
        {% load dolphin_tags %}
        {% ifactive "testing_missing" %}
        Test4
        {% else %}
        Test5
        {% endifactive %}
        """
        expected_resp = "Test5"
        self.check_res(text, expected_resp)

class FlagListTest(BaseTest):
    fixtures = ['dolphin_users.json', 'dolphin_user_flags.json', 'dolphin_base_flags.json']

    def clear(self):
        LocalStoreMiddleware.local.clear()

    def _fake_request(self):
        req = type("Request", (object,), {})()
        return req

    def test_active_flag_list(self):
        text = r"""{% load dolphin_tags %}{% active_flags %}"""
        t = Template(text)
        c = Context()

        res = t.render(c)
        self.assertEqual(res,
                         "enabled")

    def test_active_flag_list_user(self):
        text = r"""{% load dolphin_tags %}{% active_flags %}"""
        req = self._fake_request()
        req.user = User.objects.get(username="registered")
        c = Context({'request':req})
        t = Template(text)
        res = t.render(c)
        #test a registered user that is a part of the selected_group flag group
        res = res.split(',')
        res.sort()

        expected = ["enabled","registered_only","selected_group"]

        self.assertEqual(res, expected)

        self.clear()
        req.user = User.objects.get(username='staff')
        c = Context({'request':req})
        t = Template(text)
        res = t.render(c)
        #test a staff user that is not in the group expected by selected_group flag
        res = res.split(',')
        res.sort()

        expected = ["enabled","registered_only","staff_only"]
        self.assertEqual(res, expected)
