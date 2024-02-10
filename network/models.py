from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    followers = models.ManyToManyField('self', symmetrical=False, related_name='following')

    def __str__(self):
        return self.username

    def get_followers_count(self):
        return self.followers.count()

    def get_following_count(self):
        return self.following.count()

    def get_posts(self, limit=None):
        # Query all the posts related to this user and order them by timestamp
        posts = Post.objects.filter(user=self).order_by('-timestamp')
        
        if limit is not None:
            return posts[:limit]  # Limit the number of posts if 'limit' is provided
        else:
            return posts  # Return all posts if 'limit' is not provided



class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    liked_by = models.ManyToManyField(User, related_name='liked_posts', blank=True)

    def __str__(self):
        return f"Post by {self.user.username} on {self.timestamp}"

    def get_likes_count(self):
        return self.liked_by.count()

    # Define the method to check if a user has liked this post
    def user_has_liked(self, user):
        return user in self.liked_by.all()

