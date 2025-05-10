from django import views
from django.urls import include, path, re_path
from .views import add_comment, bookmarked_notes, create_post, delete_comment, delete_note, delete_notification, edit_note, enhance_content, follow_user, generate_quiz, generate_summary, home, increment_view, note_detail, notification_stream, notifications, report_comment, search_notes, toggle_bookmark, toggle_star, update_profile, update_profile_pic, user_followers, user_following, user_notes, user_profile_view, vote_comment

urlpatterns = [
    path('', home, name='home'),  # Root URL maps to home page
    path('create-post/', create_post, name='create_post'),
    path('my-notes/', user_notes, name='user_notes'),
    path('toggle-star/<int:note_id>/', toggle_star, name='toggle_star'),
    path('toggle-bookmark/<int:note_id>/', toggle_bookmark, name='toggle_bookmark'),
    path('increment-view/<int:note_id>/', increment_view, name='increment_view'),
    path('note/<int:note_id>/', note_detail, name='note_detail'),
    path('note/<int:note_id>/edit/', edit_note, name='edit_note'),
    path('note/<int:note_id>/delete/', delete_note, name='delete_note'),

    path('add-comment/<int:note_id>/', add_comment, name='add_comment'),
    path('delete-comment/<int:comment_id>/', delete_comment, name='delete_comment'),

    path('vote-comment/<int:comment_id>/', vote_comment, name='vote_comment'),
    path('report-comment/<int:comment_id>/', report_comment, name='report_comment'),


    path('generate_summary/<int:note_id>/', generate_summary, name='generate_summary'),
    # path('get_note_summaries/<int:note_id>/', get_note_summaries, name='get_note_summaries'),

    path('generate_quiz/<int:note_id>/', generate_quiz, name='generate_quiz'),

    path('search/', search_notes, name='search_notes'),

    path('notifications/', notifications, name='notifications'),
    path('notifications/delete/<int:notification_id>/', delete_notification, name='delete_notification'),
    #path('profile/', user_profile, name='user_profile'),
    path('user/<int:user_id>/', user_profile_view, name='user_profile_view'),
    # Add these to your urlpatterns
    path('follow/<int:user_id>/', follow_user, name='follow_user'),
    path('user/following/', user_following, name='user_following'),
    path('user/followers/', user_followers, name='user_followers'),
    path('notifications/stream/', notification_stream, name='notification_stream'),
    path('bookmarks/', bookmarked_notes, name='bookmarked_notes'),
    path('update-profile/', update_profile, name='update_profile'),
    path('update-profile-pic/', update_profile_pic, name='update_profile_pic'),
    path('enhance-content/', enhance_content, name='enhance_content'),

    path('followers/<int:user_id>/', user_followers, name='user_followers'),
    path('following/<int:user_id>/', user_following, name='user_following'),

    path('summernote/', include('django_summernote.urls')),
]
