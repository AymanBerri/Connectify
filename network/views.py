import json
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.core.paginator import Paginator, EmptyPage
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.middleware.csrf import get_token
from django.views import View
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from .serializers import  UserSerializer, PostSerializer

from .models import User, Post


# Classes ////////////////////////////////////////////
class FollowingPostsAPIView(APIView):
    def get(self, request, format=None):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        # Retrieve posts by users that the current user follows
        following_users = request.user.following.all()
        following_posts = Post.objects.filter(user__in=following_users).order_by('-timestamp')

        # Define the number of posts per page
        posts_per_page = 10  # Adjust as needed

        paginator = Paginator(following_posts, posts_per_page)
        page_number = request.GET.get('page')

        try:
            # Convert the page number to an integer
            try:
                page_number = int(page_number)
            except (TypeError, ValueError):
                # Handle the case when the page number is not provided or is not a valid integer
                page_number = 1  # Default to the first page

            page = paginator.page(page_number)
        except EmptyPage:
            return Response({'error': 'No more pages.'})

        serializer = PostSerializer(page, many=True, context={'request': request})
        posts_data = serializer.data

        # Serialize the logged-in user data using the UserSerializer
        logged_in_user_data = UserSerializer(request.user).data

        return Response({
            'posts': posts_data,
            'has_next': page.has_next(),
            'page_number': page.number,
            'total_pages': paginator.num_pages,
            'logged_in_user': logged_in_user_data,
        })

class PostsAPIView(APIView):
    def get(self, request, username=None, format=None):
        # If a username is provided, filter posts for that user; otherwise, get all posts
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

            posts = Post.objects.filter(user=user).order_by('-timestamp')
        else:
            posts = Post.objects.all().order_by('-timestamp')

        # Define the number of posts per page
        posts_per_page = 10  # Adjust as needed

        paginator = Paginator(posts, posts_per_page)
        page_number = request.GET.get('page')

        try:
            # Convert the page number to an integer
            try:
                page_number = int(page_number)
            except (TypeError, ValueError):
                # Handle the case when the page number is not provided or is not a valid integer
                page_number = 1  # Default to the first page

            page = paginator.page(page_number)
        except EmptyPage:
            return Response({'error': 'No more pages.'})

        serializer = PostSerializer(page, many=True, context={'request': request})
        posts_data = serializer.data

        # Serialize the logged-in user data using the UserSerializer
        logged_in_user_data = UserSerializer(request.user).data

        if username:
            # Serialize the user data for the requested user using the UserSerializer
            user_data = UserSerializer(user).data
            return Response({
                'user': user_data,
                'posts': posts_data,
                'has_next': page.has_next(),
                'page_number': page.number,
                'total_pages': paginator.num_pages,
                'logged_in_user': logged_in_user_data,
            })

        return Response({
            'posts': posts_data,
            'has_next': page.has_next(),
            'page_number': page.number,
            'total_pages': paginator.num_pages,
            'logged_in_user': logged_in_user_data,
        })

class CreateNewPostView(View):
    def post(self, request, *args, **kwargs):
        # Parse the JSON data from the request body
        data = json.loads(request.body)

        # Get the content 
        content = data.get('content', '')

        # Validate the content (e.g., check for empty content)
        if not content.strip():
            return JsonResponse({'success': False, 'message': 'Content cannot be empty'}, status=400)

        # Create the new post
        new_post = Post(user=request.user, content=content)
        new_post.save()

        return JsonResponse({'success': True, 'message': 'Post created successfully'}, status=201)  # status 201 = Rest API creation

    def get(self, request, *args, **kwargs):
        return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

class UpdatePostAPIView(APIView):
    def put(self, request, post_id, format=None):
        # Handle the PUT request to update a post's content
        post_id = post_id  # Extract post_id from the URL or request data
        new_content = request.data.get('content')

        try:
            post = Post.objects.get(pk=post_id)
            # Check if the user has permission to update this post (e.g., the post's author)

            # Update the post with the new content
            post.content = new_content
            post.save()

            # Serialize the updated post
            serializer = PostSerializer(post)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Post.DoesNotExist:
            return Response({'error': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class LikePostView(View):
    def post(self, request, post_id):
        # Check if the user is authenticated
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Authentication required'}, status=403)

        # Get the post or return a 404 response if it doesn't exist
        post = get_object_or_404(Post, id=post_id)

        # Check if the user has already liked the post
        user_has_liked = request.user in post.liked_by.all()

        if user_has_liked:
            # User has already liked the post, so unlike it
            post.liked_by.remove(request.user)
            message = 'Post unliked successfully'
        else:
            # User hasn't liked the post, so like it
            post.liked_by.add(request.user)
            message = 'Post liked successfully'

        # Calculate the current likes count
        likes_count = post.liked_by.count()

        # Return a JSON response with the success status, message, and likes count
        return JsonResponse({'success': True, 'message': message, 'likes_count': likes_count, 'user_has_liked': not user_has_liked})
    
class GetLoggedInUser(APIView):
    def get(self, request):
        if request.user.is_authenticated:
            user_serializer = UserSerializer(request.user)
            return Response({'user': user_serializer.data})
        else:
            return Response({'user': None})

class UserProfileView(APIView):
    def get(self, request, username, format=None):
        try:
            # Retrieve the user based on the provided username
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        # Serialize the user data using your UserSerializer
        serializer = UserSerializer(user)

        return Response(serializer.data)

class FollowUnfollowUserView(APIView):
    def put(self, request, username):
        user_to_follow = get_object_or_404(User, username=username)

        if request.user == user_to_follow:
            return Response({'message': 'You cannot follow/unfollow yourself.'}, status=400)

        if request.user in user_to_follow.followers.all():
            # If the user is already following, unfollow
            request.user.following.remove(user_to_follow)
            message = 'Unfollowed successfully'
        else:
            # If the user is not following, follow
            request.user.following.add(user_to_follow)
            message = 'Followed successfully'

        # Get updated follower and following counts
        followers_count = user_to_follow.get_followers_count()
        following_count = request.user.get_following_count()

        return Response({
            'message': message,
            'followers_count': followers_count,
            'following_count': following_count
        }, status=200)
    
# Functions ////////////////////////////////////////////
def index(request):
    # Authenticated users view their inbox
    if request.user.is_authenticated:
        return render(request, "network/index.html")

    # Everyone else is prompted to sign in
    else:
        return HttpResponseRedirect(reverse("login"))

def profile(request, username):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        try:
            # Query the user based on the provided username
            user_data = User.objects.get(username=username)

            # Render the user profile page and pass the user-specific data and posts to the template
            return render(request, "network/profile.html", {
                'user_data': user_data,
                })
        except User.DoesNotExist:
            # Handle the case when the user with the provided username doesn't exist
            return HttpResponseRedirect(reverse("login"))
    else:
        # Unauthenticated users are redirected to the login page
        return HttpResponseRedirect(reverse("login"))
    
@login_required
def following(request):
    return render(request, 'network/following.html')

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "network/login.html")

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


