from django.test import TestCase, Client
from json import dumps
from django.urls import reverse
from .models import User, Post
from rest_framework import status
from rest_framework.test import APIClient


class UserModelTestCase(TestCase):

    def setUp(self):
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')

    def test_get_followers_count(self):
        self.user1.followers.add(self.user2)
        self.assertEqual(self.user1.get_followers_count(), 1)

    def test_get_following_count(self):
        self.user1.following.add(self.user2)
        self.assertEqual(self.user1.get_following_count(), 1)

    # Add a new test for the user's liked posts
    def test_get_liked_posts(self):
        # Create a post
        post = Post.objects.create(user=self.user1, content='Test post')
        
        # User1 likes the post
        self.user1.liked_posts.add(post)
        
        # Check if the post is in the user's liked posts
        self.assertEqual(self.user1.liked_posts.count(), 1)
        self.assertEqual(self.user1.liked_posts.first(), post)

class PostModelTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(username='user1', password='password1')
        self.post = Post.objects.create(user=self.user, content='Test post')

    def test_get_likes_count(self):
        liking_user = User.objects.create(username='liker', password='likerpassword')
        self.post.liked_by.add(liking_user)
        self.assertEqual(self.post.get_likes_count(), 1)

    # Add a new test for checking if a post is liked by a user
    def test_user_has_liked(self):
        user2 = User.objects.create_user(username='user2', password='password2')

        # Initially, the post should not be liked by the user
        self.assertFalse(self.post.user_has_liked(user2))

        # After the user likes the post
        self.post.liked_by.add(user2)

        # The post should be liked by the user
        self.assertTrue(self.post.user_has_liked(user2))

class PostViewTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpassword')
        self.client.login(username='testuser', password='testpassword')
        self.post = Post.objects.create(user=self.user, content='Test content')

    def test_all_posts_view(self):
        response = self.client.get(reverse('all_posts_api'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test content')

    def test_create_new_post_view(self):
        data = {'content': 'New test post'}
        response = self.client.post(reverse('create_new_post'), dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 201)  # Change to 201 for successful creation
        self.assertEqual(Post.objects.count(), 2)  # Check if the new post was created

    def test_like_post_view(self):
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Post liked successfully')
        self.assertTrue(data['user_has_liked'])
        self.assertEqual(data['likes_count'], 1)

    def test_unlike_post_view(self):
        self.post.liked_by.add(self.user)  # User initially liked the post
        response = self.client.post(reverse('like_post', args=[self.post.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['message'], 'Post unliked successfully')
        self.assertFalse(data['user_has_liked'])
        self.assertEqual(data['likes_count'], 0)

    def test_pagination_controls(self):
        # for the pagination test, 21 new posts are created
        for i in range(21):
            Post.objects.create(user=self.user, content=f'Test post {i}')

        response = self.client.get(reverse('all_posts_api') + '?page=2')
        self.assertEqual(response.status_code, 200)
        data = response.json()

        # Check if the API view returns the correct number of posts per page
        self.assertEqual(len(data['posts']), 10)

        # Check if the 'has_next' flag is correctly set
        self.assertTrue(data['has_next'])

        # Check if the 'page_number' is correct
        self.assertEqual(data['page_number'], 2)

        # Check if the 'total_pages' is correct
        self.assertEqual(data['total_pages'], 3)

class UserProfileViewTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        
        # Create test posts
        self.post1 = Post.objects.create(user=self.user1, content='Post by user1')
        self.post2 = Post.objects.create(user=self.user2, content='Post by user2')

    def test_user_posts_display(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the profile page for user1
        response = self.client.get(reverse('user_posts_api', args=['user1']))
        
        # Check if user1's post is displayed in the response
        self.assertContains(response, 'Post by user1')

        # Check if user2's post is not displayed
        self.assertNotContains(response, 'Post by user2')

    def test_follow_user(self):
            self.client.login(username='user1', password='password1')
            response = self.client.put(reverse('follow_unfollow_user', args=['user2']))

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.data['message'], 'Followed successfully')

            # Check if user1 is following user2
            self.assertTrue(self.user1.following.filter(username='user2').exists())

    def test_unfollow_user(self):
        # First, let user1 follow user2
        self.user1.following.add(self.user2)

        self.client.login(username='user1', password='password1')
        response = self.client.put(reverse('follow_unfollow_user', args=['user2']))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['message'], 'Unfollowed successfully')

        # Check if user1 is no longer following user2
        self.assertFalse(self.user1.following.filter(username='user2').exists())

    def test_follow_unfollow_self(self):
        self.client.login(username='user1', password='password1')
        response = self.client.put(reverse('follow_unfollow_user', args=['user1']))

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['message'], 'You cannot follow/unfollow yourself.')

class UserProfileAndPostsTest(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(username='user1', password='password1')
        self.user2 = User.objects.create_user(username='user2', password='password2')
        
        # Create test posts
        self.post1 = Post.objects.create(user=self.user1, content='Post by user1')
        self.post2 = Post.objects.create(user=self.user2, content='Post by user2')

    def test_user_profile_display(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the user profile page for user1
        response = self.client.get(reverse('user_posts_api', args=['user1']))
        
        # Check if the user's username is displayed in the response
        self.assertContains(response, 'user1')
        
        # Check if user1's posts are displayed in the response
        self.assertContains(response, 'Post by user1')

        # Check if user2's posts are not displayed
        self.assertNotContains(response, 'Post by user2')

    def test_posts_display(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the posts page for user1
        response = self.client.get(reverse('user_posts_api', args=['user1']))
        
        # Check if user1's posts are displayed in the response
        self.assertContains(response, 'Post by user1')

        # Check if user2's posts are not displayed
        self.assertNotContains(response, 'Post by user2')

    def test_posts_display_all_users(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the posts page for all users
        response = self.client.get(reverse('all_posts_api'))
        
        # Check if user1's posts are displayed in the response
        self.assertContains(response, 'Post by user1')

        # Check if user2's posts are displayed
        self.assertContains(response, 'Post by user2')

    def test_user_profile_api(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the user profile API for user1
        response = self.client.get(reverse('user_profile_api', args=['user1']))
        
        # Check if the user's username is in the API response
        self.assertEqual(response.status_code, 200)
        self.assertIn('user1', str(response.content))
        
    def test_posts_api(self):
        # Log in as a user (you can customize this based on your authentication system)
        self.client.login(username='user1', password='password1')

        # Get the posts API for user1
        response = self.client.get(reverse('user_posts_api', args=['user1']))
        
        # Check if user1's posts are in the API response
        self.assertEqual(response.status_code, 200)
        self.assertIn('Post by user1', str(response.content))

class FollowingPageTests(TestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            password='testpassword'
        )
        # Create a test client for making API requests
        self.client = APIClient()

    def test_access_following_page_authenticated_user(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Access the "Following" page
        response = self.client.get(reverse('following'))

        # Verify that the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_access_following_page_unauthenticated_user(self):
        # Access the "Following" page without logging in
        response = self.client.get(reverse('following'))

        # Verify that the response status code is 302 (Redirect) due to not being authenticated
        self.assertEqual(response.status_code, status.HTTP_302_FOUND)

    def test_get_following_posts_authenticated_user(self):
        # Log in the user
        self.client.login(username='testuser', password='testpassword')

        # Make an API request to get following posts
        response = self.client.get(reverse('api_following_posts'))

        # Verify that the response status code is 200 (OK)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_posts_unauthenticated_user(self):
        # Make an API request to get following posts without logging in
        response = self.client.get(reverse('api_following_posts'))

        # Verify that the response status code is 401 (Unauthorized) due to not being authenticated
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


    def tearDown(self):
    # Clean up resources or database records if necessary
        self.user.delete()

