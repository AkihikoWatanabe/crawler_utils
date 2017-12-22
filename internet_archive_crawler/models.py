from django.db import models

# Create your models here.

class Url(models.Model):
    
    url_string = models.URLField()
    created_at = models.DateTimeField(
            auto_now_add=True
    )

    def __str__(self):
        return self.url_string


class PageUrl(models.Model):
    
    url = models.ForeignKey(
            Url,
            on_delete=models.CASCADE
    )
    pageurl_string = models.URLField()
    page = models.PositiveSmallIntegerField()
    status_code = models.PositiveSmallIntegerField() 
    created_at = models.DateTimeField(
            auto_now_add=True
    ) 

    def __str__(self):
        return self.pageurl_string


class Source(models.Model):

    purl = models.ForeignKey(
            PageUrl,
            on_delete=models.CASCADE
    )
    title = models.CharField(
            max_length=255
    )
    html = models.TextField()
    published_at = models.DateTimeField()

    def __str__(self):
        return self.title 
