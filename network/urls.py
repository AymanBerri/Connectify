
from django.urls import path


from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path('profile/<str:username>/', views.profile, name='user_profile'),
    path("following/", views.following, name="following"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path('get-logged-in-user/', views.GetLoggedInUser.as_view(), name='get_logged_in_user'),
    
    
    ### API Endpoints ###
    # this gets all the posts
    path('api/posts/all/', views.PostsAPIView.as_view(), name='all_posts_api'),
    # this gets all posts created by the user passed 
    path('api/posts/user/<str:username>/', views.PostsAPIView.as_view(), name='user_posts_api'),
    # this gets all the posts of the users the person follows
    path('api/posts/following/', views.FollowingPostsAPIView.as_view(), name='api_following_posts'),

    path('api/profile/<str:username>/', views.UserProfileView.as_view(), name='user_profile_api'),
    path('api/posts/create/', views.CreateNewPostView.as_view(), name='create_new_post'),
    path('api/posts/update/<int:post_id>/', views.UpdatePostAPIView.as_view(), name='update_post_api'),
    path('api/posts/like/<int:post_id>/', views.LikePostView.as_view(), name='like_post'),
    path('api/profile/<str:username>/follow/', views.FollowUnfollowUserView.as_view(), name='follow_unfollow_user'),
]

