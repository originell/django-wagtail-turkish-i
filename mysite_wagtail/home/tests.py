from wagtail.tests.utils import WagtailPageTests
from wagtail.core.models import Page

from .models import HomePage


class SlugDiacriticsTestCase(WagtailPageTests):
    def test_basic_plane(self):
        root = Page.objects.get(url_path="/home/")
        page = HomePage(title="Hello Vienna")
        root.add_child(instance=page)
        self.assertEqual(page.slug, "hello-vienna")

    def test_latin_extended(self):
        root = Page.objects.get(url_path="/home/")
        page = HomePage(title="Hello İstanbul")
        root.add_child(instance=page)
        self.assertEqual(page.slug, "hello-istanbul")
