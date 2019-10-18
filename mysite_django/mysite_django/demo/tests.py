from django.test import TestCase

from .models import Page


class SlugDiacriticsTestCase(TestCase):
    def test_basic_plane(self):
        page = Page(title="Hello Vienna")
        page.save()
        self.assertEqual(page.slug, "hello-vienna")

    def test_latin_extended(self):
        page = Page(title="Hello İstanbul")
        page.save()
        self.assertEqual(page.slug, "hello-istanbul")
