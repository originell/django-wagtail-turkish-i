from django.db import models
from django.utils.text import slugify


# Create your models here.
class Page(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(allow_unicode=True)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title, allow_unicode=True)
        return super().save(*args, **kwargs)
