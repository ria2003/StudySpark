import os
from django import forms
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from regex import F
import requests
from sympy import Sum
from urllib3 import Retry
from .forms import NoteForm
from django.http import HttpResponse, JsonResponse, FileResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
import json
from django.shortcuts import render, get_object_or_404, redirect
from .models import CommentReport, CommentVote, Follow, NoteBookmark, Notification, PostNote, NoteStar, PostFile, Comment, QuizGeneration, User
from django.db.models import Count, Q, Case, When
from django.utils import timezone
import uuid
import base64
from django.core.files.uploadedfile import UploadedFile
import logging
import os
import requests
from requests.adapters import HTTPAdapter
import json
import logging
import google.generativeai as genai
from django.db.models import Sum, Count, F, Value, IntegerField
from django.db.models.functions import Coalesce
import random
import requests
from django.template.loader import render_to_string
from django.db.models.functions import Floor

def home(request):
    if request.user.is_authenticated:

        # Fetch a random quote
        # Fetch a random quote - UPDATED API HANDLING
        quote = None
        apis = [
            'https://api.quotable.io/random',
            'https://zenquotes.io/api/random'
        ]
        
        for api_url in apis:
            try:
                response = requests.get(api_url, timeout=3)  # Add timeout
                if response.status_code == 200:
                    data = response.json()
                    if api_url.startswith('https://api.quotable.io'):
                        quote = {
                            'text': data['content'],
                            'author': data['author']
                        }
                    elif api_url.startswith('https://zenquotes.io'):
                        quote = {
                            'text': data[0]['q'],
                            'author': data[0]['a']
                        }
                    break  # Exit loop if successful
            except Exception:
                continue  # Try next API
        
        # Use fallback if all APIs fail
        if not quote:
            fallback_quotes = [
                {'text': 'The only way to do great work is to love what you do.', 'author': 'Steve Jobs'},
                {'text': "Life is what happens when you're busy making other plans.", 'author': 'John Lennon'},
                {'text': 'The future belongs to those who believe in the beauty of their dreams.', 'author': 'Eleanor Roosevelt'},
                {'text': 'In the middle of difficulty lies opportunity.', 'author': 'Albert Einstein'},
                {'text': 'Knowledge is power.', 'author': 'Francis Bacon'}
            ]
            quote = random.choice(fallback_quotes)

        # Get the selected category from query parameters
        selected_category = request.GET.get('category', None)

        following_feed = request.GET.get('following', None) == 'true'
        
        # Get all categories including 'other' subcategories
        main_categories = PostNote.objects.filter(is_public=True).exclude(
            category='other'
        ).values('category').annotate(
            count=Count('category')
        ).order_by('category')
        
        # Get 'other' category items by their specific other_category names
        other_categories = PostNote.objects.filter(
            is_public=True,
            category='other'
        ).exclude(
            other_category__isnull=True
        ).values('other_category').annotate(
            count=Count('other_category')
        ).order_by('other_category')

        # Combine all categories for display
        all_categories = list(main_categories) + [
            {'category': cat['other_category'], 'count': cat['count']} 
            for cat in other_categories
        ]

        for cat in all_categories:
            cat['category'] = cat['category'].replace("_", " ").title()

        # Get page number from request, default to 1
        page = int(request.GET.get('page', 1))
        items_per_page = 10  # Show 10 items per page
        
        # Base query for recent public notes
        recent_notes_query = PostNote.objects.filter(is_public=True)
        
        """
        # Apply category filter if selected
        if selected_category:
            # [Keep existing category filter code]
            pass
        # If no category is selected, filter by user's interests for the "For you" section
        elif not selected_category:
            # [Keep existing interests filtering code]
            pass
        
        # Apply category filter if selected
        if selected_category:
            # Convert display format back to database format
            db_category = selected_category.lower().replace(" ", "_")
            
            # Check if it's a main category or other_category
            if db_category in [choice[0] for choice in PostNote._meta.get_field('category').choices]:
                recent_notes_query = recent_notes_query.filter(category=db_category)
            else:
                recent_notes_query = recent_notes_query.filter(
                    category='other', 
                    other_category=db_category
                )
        # If no category is selected, filter by user's interests for the "For you" section
        elif not selected_category:
            # Define the mapping from interest choices to post categories
            interest_to_category_mapping = {
                "science_tech": [
                    "physics", "chemistry", "biology", "astronomy", "environmental_science", 
                    "mathematics", "computer_science", "engineering", "information_technology", 
                    "artificial_intelligence", "data_science"
                ],
                "humanities_arts": [
                    "history", "arts", "literature", "language", "philosophy", "psychology"
                ],
                "business_economy": [
                    "business", "education", "politics"
                ],
                "health_lifestyle": [
                    "health_wellness", "food_cooking", "sports_fitness", "travel_culture", 
                    "personal_development", "hobbies", "parenting"
                ],
                "entertainment_creativity": [
                    "entertainment", "design", "spirituality", "gaming"
                ],
                "other": [
                    "other"
                ]
            }
            
            # Get user's interests from the comma-separated string
            user_interests = request.user.interests.split(',') if request.user.interests else []
            
            if user_interests:
                # Build a list of categories based on user's interests
                relevant_categories = []
                for interest in user_interests:
                    if interest in interest_to_category_mapping:
                        relevant_categories.extend(interest_to_category_mapping[interest])
                
                # If the user has "Other" as an interest, include all remaining categories
                if "other" in user_interests:
                    all_possible_categories = []
                    for cats in interest_to_category_mapping.values():
                        all_possible_categories.extend(cats)
                    
                    # Remove duplicates by converting to set then back to list
                    all_categories_set = set(all_possible_categories)
                    relevant_categories_set = set(relevant_categories)
                    
                    # Add categories that are in all_categories but not in relevant_categories
                    remaining_categories = all_categories_set - relevant_categories_set
                    relevant_categories.extend(list(remaining_categories))
                
                # If user has relevant categories, filter by them
                if relevant_categories:
                    # Filter by main categories
                    main_category_filter = Q()
                    for category in [cat for cat in relevant_categories if cat != "other"]:
                        main_category_filter |= Q(category=category)
                    
                    # Filter by other_category if 'other' is in relevant_categories
                    other_category_filter = Q()
                    if "other" in relevant_categories:
                        other_category_filter = Q(category="other")
                    
                    # Combine filters
                    recent_notes_query = recent_notes_query.filter(main_category_filter | other_category_filter)

        """
        # Handle following feed (new option)
        if following_feed:
            # Get users that the current user follows
            followed_users = User.objects.filter(followers__follower=request.user)
            # Filter posts to only show those from followed users
            recent_notes_query = recent_notes_query.filter(user__in=followed_users).order_by('-created_at')
        
        # Apply category filter if selected
        elif selected_category:
            # Convert display format back to database format
            db_category = selected_category.lower().replace(" ", "_")
            
            # Check if it's a main category or other_category
            if db_category in [choice[0] for choice in PostNote._meta.get_field('category').choices]:
                recent_notes_query = recent_notes_query.filter(category=db_category)
            else:
                recent_notes_query = recent_notes_query.filter(
                    category='other', 
                    other_category=db_category
                )
        # If no category is selected and not following feed, filter by user's interests for the "For you" section
        else:  # This is the "For You" section based solely on interests
            # Define the mapping from interest choices to post categories
            interest_to_category_mapping = {
                "science_tech": [
                    "physics", "chemistry", "biology", "astronomy", "environmental_science", 
                    "mathematics", "computer_science", "engineering", "information_technology", 
                    "artificial_intelligence", "data_science"
                ],
                "humanities_arts": [
                    "history", "arts", "literature", "language", "philosophy", "psychology"
                ],
                "business_economy": [
                    "business", "education", "politics"
                ],
                "health_lifestyle": [
                    "health_wellness", "food_cooking", "sports_fitness", "travel_culture", 
                    "personal_development", "hobbies", "parenting"
                ],
                "entertainment_creativity": [
                    "entertainment", "design", "spirituality", "gaming"
                ],
                "other": [
                    "other"
                ]
            }
            
            # Get user's interests from the comma-separated string
            user_interests = request.user.interests.split(',') if request.user.interests else []
            
            if user_interests:
                # Build a list of categories based on user's interests
                relevant_categories = []
                for interest in user_interests:
                    if interest in interest_to_category_mapping:
                        relevant_categories.extend(interest_to_category_mapping[interest])
                
                # If the user has "Other" as an interest, include all remaining categories
                if "other" in user_interests:
                    all_possible_categories = []
                    for cats in interest_to_category_mapping.values():
                        all_possible_categories.extend(cats)
                    
                    # Remove duplicates by converting to set then back to list
                    all_categories_set = set(all_possible_categories)
                    relevant_categories_set = set(relevant_categories)
                    
                    # Add categories that are in all_categories but not in relevant_categories
                    remaining_categories = all_categories_set - relevant_categories_set
                    relevant_categories.extend(list(remaining_categories))
                
                # If user has relevant categories, filter by them
                if relevant_categories:
                    # Filter by main categories
                    main_category_filter = Q()
                    for category in [cat for cat in relevant_categories if cat != "other"]:
                        main_category_filter |= Q(category=category)
                    
                    # Filter by other_category if 'other' is in relevant_categories
                    other_category_filter = Q()
                    if "other" in relevant_categories:
                        other_category_filter = Q(category="other")
                    
                    # Combine filters
                    recent_notes_query = recent_notes_query.filter(main_category_filter | other_category_filter)
            else:
                # If user has no interests, show popular content
                recent_notes_query = recent_notes_query.annotate(
                    popularity_score=Count('stars') + (Count('comments') * 2) + Floor(F('views_count') / 10)
                ).order_by('-popularity_score', '-created_at')
        
        # Get filtered notes with all related data
        all_notes = recent_notes_query.select_related('user').annotate(
            star_count=Count('stars', distinct=True),
            comment_count=Count('comments', distinct=True)
        ).order_by('-created_at')

         # Calculate pagination
        start_index = (page - 1) * items_per_page
        end_index = start_index + items_per_page
        recent_notes = all_notes[start_index:end_index]
        
        # Calculate if there are more results
        has_more = len(all_notes) > end_index

        # Get first image for each note
        for note in recent_notes:
            note.preview_image = PostFile.objects.filter(
                note=note,
                file_type__startswith='image/'
            ).first()

        

        # First calculate total views
        # Update this part of your code
        top_authors = User.objects.annotate(
            # First, get a count of posts by this user
            post_count=Count('postnote', distinct=True),
            
            # Then, properly sum the views_count with distinct to avoid duplication
            total_views=Coalesce(Sum('postnote__views_count', distinct=True), Value(0)),
            total_stars=Count('postnote__stars', distinct=True)  # Use distinct=True to count unique stars
        ).filter(
            # Filter users who have at least posted something
            postnote__isnull=False
        ).distinct().order_by(
            '-total_views', '-total_stars'
        )[:5]

        # Get most recently bookmarked note (from other users)
        recent_bookmark = PostNote.objects.filter(
            bookmarks__user=request.user
        ).exclude(
            user=request.user  # Exclude self notes - use exclude instead of ne lookup
        ).order_by(
            '-bookmarks__created_at'
        ).first()  # Get the most recent one

        # Get bookmarked notes for the current user
        bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)

        starred_notes = PostNote.objects.filter(stars__user=request.user)

        # Get the list of users that the current user follows
        followed_users = User.objects.filter(followers__follower=request.user)

        context = {
            'categories': all_categories,
            'quote': quote,
            'recent_notes': recent_notes,
            'top_authors': top_authors,
            'recent_bookmark': recent_bookmark,
            'bookmarked_notes': bookmarked_notes,
            'starred_notes': starred_notes,
            'selected_category': selected_category,
            'following_feed': following_feed,
            'current_page': page,
            'has_more': has_more,
            'followed_users': followed_users
        }
        
        # If AJAX request, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # Render just the notes part to a string
            html = render_to_string('blog/note_items_partial.html', {'recent_notes': recent_notes})
            return JsonResponse({
                'html': html,
                'has_more': has_more
            })
        return render(request, 'blog/home2.html', context)
    else:

        # Fetch the last three public posts for the landing page
        last_three_posts = PostNote.objects.filter(
            is_public=True
        ).select_related('user').annotate(
            star_count=Count('stars', distinct=True)
        ).order_by('-created_at')[:3]
        
        # Get first image for each post
        for note in last_three_posts:
            note.preview_image = PostFile.objects.filter(
                note=note,
                file_type__startswith='image/'
            ).first()
            
        return render(request, 'blog/home.html', {'last_three_posts': last_three_posts})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = NoteForm(request.POST)
        
        if form.is_valid():
            try:
                note = form.save(commit=False)
                note.user = request.user
                note.save()
                
                messages.success(request, "Note posted successfully!")
                return redirect('create_post')
            
            except Exception as e:
                messages.error(request, f"Error posting note: {str(e)}")
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = NoteForm()
    
    return render(request, 'blog/create_post.html', {'form': form})



@login_required
def user_notes(request):
    # Fetch user's notes with star and file counts
    notes = PostNote.objects.filter(user=request.user).annotate(
        star_count=Count('stars'),
        file_count=Count('files'),
        comment_count=Count('comments')
    ).order_by('-created_at')

    bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)

    return render(request, 'blog/user_notes.html', {
        'notes': notes,
        'bookmarked_notes': bookmarked_notes
    })

@login_required
def note_detail(request, note_id):
    note = PostNote.objects.annotate(comment_count=Count('comments')).get(id=note_id)
    
    # Get bookmarked notes for the current user
    bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)

    starred_notes = PostNote.objects.filter(stars__user=request.user)
    
    # Only increment view count if viewer is not the note owner
    if request.user != note.user:
        note.views_count += 1
        note.save()
    
    # Get comments
    comments = Comment.objects.filter(note=note, parent=None)

    # Get the latest 5 posts from the same user (excluding the current post)
    related_notes = PostNote.objects.filter(
        user=note.user,
        is_public=True
    ).exclude(
        id=note_id
    ).order_by('-created_at')[:5]
    
    return render(request, 'blog/note_detail.html', {
        'note': note,
        'comments': comments,
        'bookmarked_notes': bookmarked_notes,
        'starred_notes' : starred_notes,
        'related_notes': related_notes  
    })
    

@login_required
def toggle_star(request, note_id):
    note = get_object_or_404(PostNote, id=note_id)
    star, created = NoteStar.objects.get_or_create(
        user=request.user, 
        note=note
    )

    # Create notification if the star was created (not toggled off)
    if created and request.user != note.user:
        Notification.objects.create(
            recipient=note.user,
            sender=request.user,
            notification_type=Notification.TYPE_STAR,
            note=note,
            message=f"{request.user.username} starred your note '{note.title}'"
        )
        
    
    starred = created  # If created is True, star was added
    
    if not created:
        star.delete()
        starred = False
    
    # Get updated star count
    star_count = NoteStar.objects.filter(note=note).count()
    
    # Check if this is an AJAX request
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'starred': starred,
            'star_count': star_count
        })
    
    # If not AJAX, do the regular redirect
    referer = request.META.get('HTTP_REFERER', '')
    if f'/note/{note_id}' in referer:
        return redirect('note_detail', note_id=note_id)
    return redirect('user_notes')

@login_required
def increment_view(request, note_id):
    note = get_object_or_404(PostNote, id=note_id)
    note.views_count += 1
    note.save()
    return redirect('note_detail') 


@login_required
def edit_note(request, note_id):
    note = get_object_or_404(PostNote, id=note_id, user=request.user)
    files = PostFile.objects.filter(note=note)
    
    if request.method == 'POST':
        form = NoteForm(request.POST, instance=note)
        new_files = request.FILES.getlist('files')
        
        print("POST data tags:", request.POST.get('tags'))
        print("Form data before validation:", form.data.get('tags'))
        
        # File size validations...
        total_file_size = sum(file.size for file in new_files)
        existing_files_size = sum(file.file_size for file in files)
        
        if total_file_size + existing_files_size > PostFile.NOTE_MAX_TOTAL_FILE_SIZE:
            messages.error(request, f"Total file size exceeds {PostFile.NOTE_MAX_TOTAL_FILE_SIZE / (1024*1024)}MB")
            return render(request, 'blog/edit_note.html', {'form': form, 'note': note, 'files': files})
        
        for file in new_files:
            if file.size > PostFile.MAX_SINGLE_FILE_SIZE:
                messages.error(request, f"File {file.name} exceeds {PostFile.MAX_SINGLE_FILE_SIZE / (1024*1024)}MB limit")
                return render(request, 'blog/edit_note.html', {'form': form, 'note': note, 'files': files})
        
        if form.is_valid():
            try:
                
                # Save the form instead of the note directly
                note = form.save(commit=False)
                
                # Now save the note with all form data
                note.save()
                
                # Save the tags from the form
                form.save_m2m()  # This is needed if you have any ManyToMany fields
                
                # Handle new file uploads
                for file in new_files:
                    PostFile.objects.create(
                        note=note,
                        filename=file.name,
                        file_type=file.content_type,
                        file_data=file.read(),
                        file_size=file.size
                    )
                
                # Force a refresh from the database
                note.refresh_from_db()
                
                # Final debug check
                print("Tags after refresh:", note.tags)
                
                messages.success(request, "Note updated successfully!")
                return redirect('note_detail', note_id=note_id)
            
            except Exception as e:
                print("Error during save:", str(e))  # Debug: Print any exceptions
                messages.error(request, f"Error updating note: {str(e)}")
        else:
            print("Form errors:", form.errors)  # Debug: Print form errors
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = NoteForm(instance=note)
        
        # If note.category is 'other', make sure other_category field is displayed
        if note.category == 'other':
            form.initial['other_category'] = note.other_category
    
    return render(request, 'blog/edit_note.html', {
        'form': form,
        'note': note,
        'files': files
    })

@login_required
def delete_note(request, note_id):
    note = get_object_or_404(PostNote, id=note_id, user=request.user)
    if request.method == 'POST':
        note.delete()
        return redirect('user_notes')
    return redirect('note_detail', note_id=note_id)

@login_required
def add_comment(request, note_id):
    note = get_object_or_404(PostNote, id=note_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        parent_id = request.POST.get('parent_id')
        
        if content:
            comment = Comment.objects.create(
                note=note,
                user=request.user,
                content=content,
                parent_id=parent_id if parent_id else None
            )

            # Create notification for note owner if commenter is not the owner
            if request.user != note.user:
                Notification.objects.create(
                    recipient=note.user,
                    sender=request.user,
                    notification_type=Notification.TYPE_COMMENT,
                    note=note,
                    comment=comment,
                    message=f"{request.user.username} commented on your note '{note.title}'"
                )
            
            # Create notification for parent comment owner if this is a reply
            if parent_id:
                parent_comment = Comment.objects.get(id=parent_id)
                if parent_comment.user != request.user and parent_comment.user != note.user:
                    Notification.objects.create(
                        recipient=parent_comment.user,
                        sender=request.user,
                        notification_type=Notification.TYPE_COMMENT_REPLY,
                        note=note,
                        comment=comment,
                        message=f"{request.user.username} replied to your comment on '{note.title}'"
                    )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'success',
                    'comment_id': comment.id,
                    'user': comment.user.username,
                    'content': comment.content,
                    'created_at': comment.created_at.strftime("%B %d, %Y %I:%M %p"),
                    'parent_id': parent_id
                })
                
    return redirect('note_detail', note_id=note_id)

@login_required
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    note_id = comment.note.id
    comment.delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
        
    return redirect('note_detail', note_id=note_id)



@login_required
def toggle_bookmark(request, note_id):
    note = get_object_or_404(PostNote, id=note_id)
    bookmark, created = NoteBookmark.objects.get_or_create(user=request.user, note=note)
    
    if not created:
        bookmark.delete()
        is_bookmarked = False
    else:
        is_bookmarked = True

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'is_bookmarked': is_bookmarked
        })
    
    referer = request.META.get('HTTP_REFERER', '')
    return redirect(referer or 'user_notes')


@login_required
def vote_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        vote_type = int(request.POST.get('vote_type', 1))  # 1 for upvote
        
        vote, created = CommentVote.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={'vote_type': vote_type}
        )

        # Create notification if this is a new upvote
        if created and vote_type == 1 and request.user != comment.user:
            Notification.objects.create(
                recipient=comment.user,
                sender=request.user,
                notification_type=Notification.TYPE_COMMENT_LIKE,
                note=comment.note,
                comment=comment,
                message=f"{request.user.username} liked your comment on '{comment.note.title}'"
            )
        
        if not created:
            # If user already voted, remove their vote (toggle behavior)
            vote.delete()
        
        return JsonResponse({
            'status': 'success',
            'vote_count': comment.get_vote_count()
        })
    
    return JsonResponse({'status': 'error'}, status=400)

@login_required
def report_comment(request, comment_id):
    if request.method == 'POST':
        comment = get_object_or_404(Comment, id=comment_id)
        reason = request.POST.get('reason')
        details = request.POST.get('details', '')
        
        if reason not in dict(CommentReport.REPORT_REASONS):
            return JsonResponse({'status': 'error', 'message': 'Invalid reason'}, status=400)
        
        report, created = CommentReport.objects.get_or_create(
            user=request.user,
            comment=comment,
            defaults={
                'reason': reason,
                'details': details
            }
        )
        
        if not created:
            return JsonResponse({'status': 'error', 'message': 'Already reported'}, status=400)
        
        return JsonResponse({'status': 'success'})
    
    return JsonResponse({'status': 'error'}, status=400)



@login_required
@require_POST
def generate_summary(request, note_id):
    logger = logging.getLogger(__name__)
    try:
        # Configure Gemini API
        genai.configure(api_key='AIzaSyC25rIRn5BegOUq5lYvj1p2CMPwhPDAGrQ')
        
        # Fetch note
        note = PostNote.objects.get(id=note_id)
        
        # Check if content exists
        if not note.main_content:
            return JsonResponse({
                'status': 'error', 
                'message': 'No content to summarize'
            }, status=400)
        
        # Get summary type from request
        summary_type = request.GET.get('type', 'brief')
        
        # Content length for metrics
        content_length = len(note.main_content)
        
        def generate_complete_summary(model, full_prompt, generation_config, summary_type):
            """
            Generate a complete summary that ensures proper ending and coherence.
            """
            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    # Generate initial summary
                    response = model.generate_content(
                        full_prompt,
                        generation_config=generation_config
                    )
                    
                    # Check for safety issues
                    if response.prompt_feedback.block_reason:
                        raise ValueError('Content blocked due to safety concerns')
                    
                    summary_text = response.text.strip()
                    
                    # For key points, we don't need additional validation
                    if summary_type == 'keypoints':
                        return summary_text
                    
                    # Validate summary completion
                    if summary_type == 'detailed':
                        # For detailed summaries, ensure comprehensive coverage
                        validation_prompt = f"""
                        Review the following summary and assess if it:
                        - Fully captures the main ideas
                        - Has a clear beginning, middle, and end
                        - Provides comprehensive insights
                        - Concludes logically
                        - Has no filler or unecessary text

                        Summary to validate:
                        {summary_text}

                        Respond with 'COMPLETE' if the summary is comprehensive and well-structured, 
                        or suggest specific improvements if not.
                        """
                    else:
                        # For brief summaries, ensure conciseness and key points
                        validation_prompt = f"""
                        Review the following summary and assess if it:
                        - Captures the most essential information
                        - Is concise and to the point
                        - Has a clear, complete thought
                        - Ends with a definitive statement

                        Summary to validate:
                        {summary_text}

                        Respond with 'COMPLETE' if the summary is concise and well-structured, 
                        or suggest specific improvements if not.
                        """
                    
                    # Validate summary
                    validation_config = {
                        'temperature': 0.2,
                        'max_output_tokens': 150
                    }
                    validation_response = model.generate_content(
                        validation_prompt,
                        generation_config=validation_config
                    )
                    
                    validation_text = validation_response.text.strip().upper()
                    
                    # If summary is complete, return it
                    if 'COMPLETE' in validation_text:
                        return summary_text
                    
                    # If not complete, adjust prompt and retry
                    if summary_type == 'detailed':
                        full_prompt += "\n\nEnsure the summary is comprehensive, provides deep insights, and has a clear concluding statement without any filler words."
                    else:
                        full_prompt += "\n\nEnsure the summary is extremely concise, captures only the most critical points, and ends with a definitive summary statement without any filler words."
                    
                    # Slightly increase temperature for creativity
                    generation_config['temperature'] = min(generation_config['temperature'] + 0.1, 0.7)
                
                except Exception as e:
                    logger.error(f"Summary generation attempt {attempt + 1} failed: {e}")
                    
                    # If last attempt, use a fallback
                    if attempt == max_attempts - 1:
                        return "Unable to generate a complete summary. Please try again."
            
            return summary_text
        
        # Determine generation parameters based on summary type
        if summary_type == 'detailed':
            prompt_instruction = """
            Create a comprehensive, professional summary that:
            - Thoroughly captures the most important ideas
            - Offers substantive context and nuanced insights
            - Ensures a clear, logical flow of information
            Eliminate all unnecessary filler words like "this article", "this guide", etc.
            """
            generation_config = {
                'temperature': 0.2,
                'max_output_tokens': 1000
            }
        elif summary_type == 'keypoints':
            prompt_instruction = """
            Extract the most important key points from the content as a bulleted list. For each key point:
            - Focus on core concepts, arguments, and facts
            - Use concise language that preserves the original meaning
            - Present each point as a complete thought
            - Ensure points are distinct from each other
            - Include only the most essential information
            - Format as a Markdown bulleted list (using * or - for each point)
            - Include 5-10 key points depending on content length and complexity
            Eliminate all unnecessary filler words like "this article", "this guide", etc.
            """
            generation_config = {
                'temperature': 0.1,
                'max_output_tokens': 800
            }
        else:  # brief summary
            prompt_instruction = """
            Create an extremely concise summary that:
            - Distills the absolute core essence of the content
            - Highlights only the most critical points
            - Uses minimal, precise language
            - Provides an instant understanding
            - Ends with a crisp, definitive statement
            Eliminate all unnecessary filler words like "this article", "this guide", etc.
            Focus exclusively on key information
            """
            generation_config = {
                'temperature': 0.1,
                'max_output_tokens': 500
            }
        
        # Prepare the full prompt
        full_prompt = f"{prompt_instruction}\n\nText to summarize:\n{note.main_content}"
        
        # Create Gemini model
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generate complete summary
        summary_text = generate_complete_summary(
            model, 
            full_prompt, 
            generation_config, 
            summary_type
        )
        
        return JsonResponse({
            'status': 'success', 
            'summary': summary_text,
            'content_length': content_length,
            'summary_length': len(summary_text),
            'summary_type': summary_type
        })
    
    except Exception as e:
        logger.exception(f"Unexpected error in generate_summary: {e}")
        return JsonResponse({
            'status': 'error', 
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def generate_quiz(request, note_id):
    logger = logging.getLogger(__name__)
    try:
        # Parse request data
        data = json.loads(request.body)
        quiz_type = data.get('quiz_type', 'basic')
        question_count = int(data.get('question_count', 5))
        
        # Validate question count
        if question_count not in [10, 15, 20]:
            question_count = 5  # Default to 5 if invalid
        
        # Configure Gemini API
        genai.configure(api_key='AIzaSyC25rIRn5BegOUq5lYvj1p2CMPwhPDAGrQ')
        
        # Fetch note
        note = PostNote.objects.get(id=note_id)
        
        # Check if content exists
        if not note.main_content:
            return JsonResponse({
                'status': 'error', 
                'message': 'No content to generate quiz from'
            }, status=400)
        
        # Create system prompt based on quiz type
        if quiz_type == 'advanced':
            system_prompt = f"""
            Create a challenging quiz about the following content, with {question_count} multiple-choice questions.
            Make the questions require deeper understanding, application of concepts, or analysis of information.
            Include questions that test higher-order thinking rather than just recall.
            
            For each question:
            1. Create a clear, thoughtful question
            2. Create balanced coverage across all topics with no major concepts omitted
            3. Provide exactly 4 options (labeled as A, B, C, D or as options 0-3)
            4. Make sure all options are plausible but only one is correct
            5. Indicate the correct answer
            
            Format the response as a valid JSON object with this structure:
            {{
                "questions": [
                    {{
                        "question": "Question text here?",
                        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                        "correct_answer": 0  // Index of correct option (0-3)
                    }},
                    // more questions...
                ]
            }}
            
            Ensure all questions relate directly to the content provided and cover all key concepts. The JSON must be valid with no syntax errors.

            """
        else:  # Basic quiz
            system_prompt = f"""
            Create a basic quiz about the entire following content, with {question_count} multiple-choice questions.
            Focus on the main ideas, key terms, and fundamental concepts from the content.
            
            For each question:
            1. Create a clear, straightforward question testing basic comprehension
            2. Create balanced coverage across all topics with no major concepts omitted
            3. Provide exactly 4 options (labeled as A, B, C, D or as options 0-3)
            4. Make sure all options are plausible but only one is correct
            5. Indicate the correct answer
            
            Format the response as a valid JSON object with this structure:
            {{
                "questions": [
                    {{
                        "question": "Question text here?",
                        "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                        "correct_answer": 0  // Index of correct option (0-3)
                    }},
                    // more questions...
                ]
            }}
            
            Ensure all questions relate directly to the content provided and cover all key concepts. The JSON must be valid with no syntax errors.

            """
        
        # Prepare the full prompt
        full_prompt = f"{system_prompt}\n\nContent to quiz on:\n{note.main_content}"
        
        # Create Gemini model - using flash for faster response
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Generation configuration - optimized for structured output
        generation_config = {
            'temperature': 0.2,
            'max_output_tokens': 2048,
            'response_mime_type': 'application/json'
        }
        
        # Generate quiz questions
        response = model.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        # Parse JSON response
        try:
            # Handle potential JSON string in text
            response_text = response.text.strip()
            
            # If response is wrapped in ```json and ``` markers, extract just the JSON
            if response_text.startswith('```json') and response_text.endswith('```'):
                response_text = response_text[7:-3].strip()
            elif response_text.startswith('```') and response_text.endswith('```'):
                response_text = response_text[3:-3].strip()
                
            quiz_data = json.loads(response_text)
            
            # Validate structure
            if not isinstance(quiz_data, dict) or 'questions' not in quiz_data:
                raise ValueError("Invalid quiz structure")
                
            # Record quiz generation in database (optional)
            QuizGeneration.objects.create(
                note=note,
                user=request.user,
                quiz_type=quiz_type,
                question_count=question_count
            )
            
            return JsonResponse({
                'status': 'success',
                'quiz': quiz_data
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}")
            logger.error(f"Raw response: {response.text}")
            return JsonResponse({
                'status': 'error',
                'message': 'Failed to parse quiz data. Please try again.'
            }, status=500)
            
    except Exception as e:
        logger.exception(f"Unexpected error in generate_quiz: {e}")
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)
    
@login_required
def search_notes(request):
    query = request.GET.get('q', '')
    
    if query:
        # Split query into keywords for more flexible matching
        keywords = query.split()
        
        # Start with an empty Q object to build complex OR conditions
        search_query = Q()
        
        # Add each keyword as a search condition
        for keyword in keywords:
            search_query |= Q(title__icontains=keyword) | \
                           Q(tags__icontains=keyword)  
        
        # Apply the combined search query
        search_results = PostNote.objects.filter(
            search_query,
            is_public=True
        ).distinct().select_related('user').annotate(
            star_count=Count('stars', distinct=True),
            comment_count=Count('comments', distinct=True)
        ).order_by('-created_at')
        
        # Get user's starred and bookmarked notes to highlight them in UI
        if request.user.is_authenticated:
            # These lines were causing the error - fixing based on home view
            starred_notes = PostNote.objects.filter(stars__user=request.user)
            bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)
        else:
            starred_notes = PostNote.objects.none()
            bookmarked_notes = PostNote.objects.none()
        
        # Get first image for each note
        for note in search_results:
            note.preview_image = PostFile.objects.filter(
                note=note,
                file_type__startswith='image/'
            ).first()
        
        # Get most viewed notes
        most_viewed = PostNote.objects.filter(
            is_public=True
        ).order_by('-views_count')[:5]

        # Get most starred notes
        most_starred = PostNote.objects.filter(
            is_public=True
        ).annotate(
            star_count=Count('stars')
        ).order_by('-star_count')[:5]
            
    else:
        search_results = []
        starred_notes = PostNote.objects.none()
        bookmarked_notes = PostNote.objects.none()
        most_viewed = PostNote.objects.filter(is_public=True).order_by('-views_count')[:5]
        most_starred = PostNote.objects.filter(is_public=True).annotate(
            star_count=Count('stars')
        ).order_by('-star_count')[:5]
    
    return render(request, 'search_results.html', {
        'search_results': search_results,
        'query': query,
        'starred_notes': starred_notes,
        'bookmarked_notes': bookmarked_notes,
        'most_viewed': most_viewed,
        'most_starred': most_starred
    })


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.cache import cache
from .models import Notification
@login_required
def notifications(request):
    # Get all notifications for the current user
    notifications = Notification.objects.filter(recipient=request.user)
    
    # Mark all notifications as read when the page is visited
    unread_count = notifications.filter(is_read=False).count()
    if unread_count > 0:
        notifications.filter(is_read=False).update(is_read=True)
        
        # Update session
        request.session['unread_notifications_count'] = 0
        
        # Update cache for SSE
        cache.set(f'user_{request.user.id}_notifications', 0, timeout=None)
    
    context = {
        'notifications': notifications
    }
    return render(request, 'blog/notifications.html', context)

# Keep this function - it's your existing view for deleting notifications
@login_required
def delete_notification(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.delete()
    
    # After deletion, recalculate unread count
    unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    request.session['unread_notifications_count'] = unread_count
    
    # Update cache for SSE
    cache.set(f'user_{request.user.id}_notifications', unread_count, timeout=None)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success', 'unread_count': unread_count})
    
    return redirect('notifications')

# ADD this new function - SSE endpoint for real-time notifications
@csrf_exempt
@login_required
def notification_stream(request):
    def event_stream():
        if request.user.is_authenticated:
            # Send initial count
            count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            yield f"data: {count}\n\n"
            
    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # For NGINX
    return response

# ADD this utility function - call this whenever a notification is created
def update_notification_count(user):
    """
    Update the notification count in cache when a new notification is created
    Call this function whenever you create a new notification
    """
    if user.is_authenticated:
        count = Notification.objects.filter(recipient=user, is_read=False).count()
        cache.set(f'user_{user.id}_notifications', count, timeout=None)
        return count
    return 0
'''
@login_required
def user_profile(request):
    # Get user information
    user = request.user
    
    # Get all posts by the user
    user_posts = PostNote.objects.filter(user=user, is_public=True).annotate(
        star_count=Count('stars'),
        comment_count=Count('comments')
    ).order_by('-created_at')
    
    # Get top 3 most starred posts
    most_starred = PostNote.objects.filter(
        user=user
    ).annotate(
        star_count=Count('stars')
    ).order_by('-star_count')[:3]
    
    # Get top 3 most viewed posts
    most_viewed = PostNote.objects.filter(
        user=user
    ).order_by('-views_count')[:3]
    
    # Get statistics
    total_posts = user_posts.count()
    total_stars = NoteStar.objects.filter(note__user=user).count()
    total_views = user_posts.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_comments = Comment.objects.filter(note__user=user).count()
    
    # Get first image for preview in posts
    for note in user_posts:
        note.preview_image = PostFile.objects.filter(
            note=note,
            file_type__startswith='image/'
        ).first()

    # Get bookmarked notes for the current user
        bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)

        starred_notes = PostNote.objects.filter(stars__user=request.user)
    
    context = {
        'user': user,
        'user_posts': user_posts,
        'most_starred': most_starred,
        'most_viewed': most_viewed,
        'total_posts': total_posts,
        'total_stars': total_stars,
        'total_views': total_views,
        'total_comments': total_comments,
        'bookmarked_notes': bookmarked_notes,
        'starred_notes': starred_notes
    }
    
    return render(request, 'blog/user_profile.html', context)
'''

def user_profile_view(request, user_id):
    # Get the requested user
    user = get_object_or_404(User, id=user_id)

    # Get user profile picture URL
    user_profile_pic = user.profile_pic.url if hasattr(user, 'profile_pic') and user.profile_pic else None
    
    # Get all public posts by the user
    user_posts = PostNote.objects.filter(user=user, is_public=True).annotate(
        star_count=Count('stars'),
        comment_count=Count('comments')
    ).order_by('-created_at')
    
    # Calculate top performing posts by combining stars and views
    # First, get all posts with their star count
    posts_with_metrics = PostNote.objects.filter(
        user=user, is_public=True
    ).annotate(
        star_count=Count('stars')
    )
    
    # Create a list to calculate performance scores
    top_performing = []
    for post in posts_with_metrics:
        # Calculate performance score (50% weight to stars, 50% to views)
        # Normalized to give more balanced results
        performance_score = (post.star_count * 10) + post.views_count
        
        # Add performance score to post object
        post.performance_score = performance_score
        top_performing.append(post)
    
    # Sort by performance score and get top 3
    top_performing = sorted(top_performing, key=lambda x: x.performance_score, reverse=True)[:3]
    
    # Get statistics
    total_posts = user_posts.count()
    total_stars = NoteStar.objects.filter(note__user=user).count()
    total_views = user_posts.aggregate(Sum('views_count'))['views_count__sum'] or 0
    total_comments = Comment.objects.filter(note__user=user).count()
    
    # Get first image for preview in posts
    for note in user_posts:
        note.preview_image = PostFile.objects.filter(
            note=note,
            file_type__startswith='image/'
        ).first()

    # Get bookmarked notes for the current user
    bookmarked_notes = PostNote.objects.filter(bookmarks__user=request.user)
    
    # Get starred notes for the current user
    starred_notes = PostNote.objects.filter(stars__user=request.user)

    # Check if the current user is following this profile
    is_following = Follow.objects.filter(
        follower=request.user, followed=user
    ).exists() if request.user.is_authenticated else False
    
    # Get follower and following counts
    follower_count = Follow.objects.filter(followed=user).count()
    following_count = Follow.objects.filter(follower=user).count()
    
    context = {
        'user': user,
        'user_profile_pic': user_profile_pic,
        'user_posts': user_posts,
        'top_performing': top_performing,  # Changed from most_starred and most_viewed
        'total_posts': total_posts,
        'total_stars': total_stars,
        'total_views': total_views,
        'total_comments': total_comments,
        'bookmarked_notes': bookmarked_notes,
        'starred_notes': starred_notes,
        'is_owner': user == request.user,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
        'profile_user': user,  # Added to ensure follow button works correctly
    }
    
    return render(request, 'blog/user_profile.html', context)

@login_required
def follow_user(request, user_id):
    user_to_follow = get_object_or_404(User, id=user_id)
    
    # Prevent users from following themselves
    if request.user == user_to_follow:
        messages.error(request, "You cannot follow yourself.")
        return redirect('user_profile_view', user_id=user_id)
    
    # Check if already following
    follow_exists = Follow.objects.filter(follower=request.user, followed=user_to_follow).exists()
    
    if follow_exists:
        Follow.objects.filter(follower=request.user, followed=user_to_follow).delete()
        #messages.success(request, f"You have unfollowed {user_to_follow.username}.")
    else:
        # Create the follow relationship
        Follow.objects.create(follower=request.user, followed=user_to_follow)
        
        # Create notification for the user being followed
        Notification.objects.create(
            recipient=user_to_follow,
            sender=request.user,
            notification_type=Notification.TYPE_FOLLOWED,
            message=f"{request.user.username} started following you"
        )
        
        # Create notification for the user who is following (optional)
        Notification.objects.create(
            recipient=request.user,
            sender=user_to_follow,
            notification_type=Notification.TYPE_FOLLOWING,
            message=f"You started following {user_to_follow.username}"
        )
        
        #messages.success(request, f"You are now following {user_to_follow.username}.")
    
    # Handle AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Get updated follower count
        follower_count = Follow.objects.filter(followed=user_to_follow).count()
        return JsonResponse({
            'is_following': not follow_exists,
            'follower_count': follower_count
        })
    
    # Try to determine the referring page
    referer = request.META.get('HTTP_REFERER', '')
    
    # If it appears the request came from the home page, redirect there
    if 'home' in referer and not 'user_profile' in referer:
        return redirect('home')
    
    # Default to redirecting to the user's profile
    return redirect('user_profile_view', user_id=user_id)

@login_required
def user_following(request):
    following = Follow.objects.filter(follower=request.user).select_related('followed')
    return render(request, 'blog/user_following.html', {'following': following})

@login_required
def user_followers(request):
    followers = Follow.objects.filter(followed=request.user).select_related('follower')
    return render(request, 'blog/user_followers.html', {'followers': followers})

@login_required
def bookmarked_notes(request):
    # Get all bookmarks by the current user for notes created by other users
    # Using your existing pattern of fetching bookmarked notes
    bookmarked_notes = PostNote.objects.filter(
        bookmarks__user=request.user,
        is_public=True
    ).select_related('user').annotate(
        star_count=Count('stars', distinct=True),
        comment_count=Count('comments', distinct=True)
    ).order_by('-bookmarks__created_at')  # Order by bookmark date
    
    # Get the selected category from query parameters
    selected_category = request.GET.get('category', None)
    
    # Get all categories including 'other' subcategories
    main_categories = PostNote.objects.filter(is_public=True).exclude(
        category='other'
    ).values('category').annotate(
        count=Count('category')
    ).order_by('category')
    
    # Get 'other' category items by their specific other_category names
    other_categories = PostNote.objects.filter(
        is_public=True,
        category='other'
    ).exclude(
        other_category__isnull=True
    ).values('other_category').annotate(
        count=Count('other_category')
    ).order_by('other_category')

    # Combine all categories for display
    all_categories = list(main_categories) + [
        {'category': cat['other_category'], 'count': cat['count']} 
        for cat in other_categories
    ]

    for cat in all_categories:
        cat['category'] = cat['category'].replace("_", " ").title()
    
    # Apply category filter if selected
    if selected_category:
        # Convert display format back to database format
        db_category = selected_category.lower().replace(" ", "_")
        
        # Check if it's a main category or other_category
        if db_category in [choice[0] for choice in PostNote._meta.get_field('category').choices]:
            bookmarked_notes = bookmarked_notes.filter(category=db_category)
        else:
            bookmarked_notes = bookmarked_notes.filter(
                category='other', 
                other_category=db_category
            )
    
    # Get first image for each note
    for note in bookmarked_notes:
        note.preview_image = PostFile.objects.filter(
            note=note,
            file_type__startswith='image/'
        ).first()
    
    context = {
        'bookmarked_notes': bookmarked_notes,
        'categories': all_categories,
        'selected_category': selected_category
    }
    
    return render(request, 'blog/bookmarked_notes.html', context)


# views.py

import json
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@login_required
@require_POST
def update_profile(request):
    """Handle profile update requests for text fields (username, about_me)"""
    try:
        data = json.loads(request.body)
        field = data.get('field')
        value = data.get('value')
        
        user = request.user
        
        if field == 'username':
            # Check if username is available
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            if User.objects.filter(username=value).exclude(id=user.id).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'This username is already taken.',
                    'original_username': user.username
                })
            
            # Update username
            user.username = value
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Username updated successfully.'
            })
            
        elif field == 'about_me':
            # Update about_me field
            user.about_me = value
            user.save()
            
            return JsonResponse({
                'status': 'success',
                'message': 'Bio updated successfully.'
            })
            
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid field specified.'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def update_profile_pic(request):
    """Handle profile picture update requests"""
    try:
        if 'profile_pic' not in request.FILES:
            return JsonResponse({
                'status': 'error',
                'message': 'No file uploaded'
            }, status=400)
        
        user = request.user
        
        # Handle the file upload
        profile_pic = request.FILES['profile_pic']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/png', 'image/gif']
        if profile_pic.content_type not in allowed_types:
            return JsonResponse({
                'status': 'error',
                'message': 'Only JPEG, PNG and GIF images are allowed.'
            }, status=400)
            
        # Validate file size (limit to 5MB)
        if profile_pic.size > 5 * 1024 * 1024:  # 5MB in bytes
            return JsonResponse({
                'status': 'error',
                'message': 'Image size should be less than 5MB.'
            }, status=400)
        
        # Save the new profile picture
        user.profile_pic = profile_pic
        user.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Profile picture updated successfully.',
            'profile_pic_url': user.profile_pic.url
        })
        
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=500)