import base64
import re
from django.db import models
from django.conf import settings

class PostNote(models.Model):
    CATEGORY_CHOICES = [
        ('physics', 'Physics'),
        ('chemistry', 'Chemistry'),
        ('biology', 'Biology'),
        ('astronomy', 'Astronomy'),
        ('environmental_science', 'Environmental Science'),
        ('mathematics', 'Mathematics'),
        ('computer_science', 'Computer Science'),
        ('engineering', 'Engineering'),
        ('information_technology', 'Information Technology'),
        ('artificial_intelligence', 'Artificial Intelligence'),
        ('data_science', 'Data Science'),
        ('history', 'History'),
        ('arts', 'Arts'),
        ('literature', 'Literature'),
        ('business', 'Business'),
        ('health_wellness', 'Health & Wellness'),
        ('language', 'Language'),
        ('travel_culture', 'Travel & Culture'),
        ('personal_development', 'Personal Development'),
        ('hobbies', 'Hobbies'),
        ('education', 'Education'),
        ('politics', 'Politics'),
        ('philosophy', 'Philosophy'),
        ('psychology', 'Psychology'),
        ('food_cooking', 'Food & Cooking'),
        ('sports_fitness', 'Sports & Fitness'),
        ('entertainment', 'Entertainment'),
        ('design', 'Design'),
        ('spirituality', 'Spirituality'),
        ('parenting', 'Parenting'),
        ('gaming', 'Gaming'),
        ('other', 'Other'),
    ]

    main_content = models.TextField(
        blank=True, 
        null=True, 
        max_length=50000  # Approximately 50,000 characters
    )

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    other_category = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField()
    main_content = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, null=True, help_text="Separate tags with commas")
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    views_count = models.IntegerField(default=0)

    def __str__(self):
        return self.title
    
    def get_first_content_image(self):
        """Extract the first image from main_content and return its src"""
        if not self.main_content:
            return None
            
        # More inclusive patterns for both HTML and Markdown
        html_pattern = r'<img[^>]+src=[\'"]([^\'"]+)[\'"]'
        markdown_pattern = r'!\[.*?\]\(([^\)]+)\)'
        
        # Try HTML pattern first
        html_match = re.search(html_pattern, self.main_content)
        if html_match:
            return html_match.group(1)
            
        # Try Markdown pattern if HTML pattern fails
        markdown_match = re.search(markdown_pattern, self.main_content)
        if markdown_match:
            return markdown_match.group(1)
            
        return None

    def get_first_content_image_data(self):
        """Return a tuple of (file_type, base64_data) for the first image"""
        image_src = self.get_first_content_image()
        if not image_src:
            return None, None
            
        # Handle base64 encoded images
        if image_src.startswith('data:'):
            try:
                # Extract file type and base64 data
                file_type = re.search(r'data:(image\/[^;]+);base64,', image_src).group(1)
                base64_data = re.search(r'base64,(.+)', image_src).group(1)
                return file_type, base64_data
            except (AttributeError, IndexError):
                return None, None
        
        # For regular URLs, just return the URL itself
        return 'url', image_src

    class Meta:
        ordering = ['-created_at']

class PostFile(models.Model):
    NOTE_MAX_TOTAL_FILE_SIZE = 50 * 1024 * 1024  # 50MB total limit
    MAX_SINGLE_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file

    note = models.ForeignKey(PostNote, on_delete=models.CASCADE, related_name='files')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100)
    file_data = models.BinaryField(default=b'')  # Store file directly in PostgreSQL
    uploaded_at = models.DateTimeField(auto_now_add=True)
    file_size = models.IntegerField()

    def __str__(self):
        return f"{self.note.title} - {self.filename}"

    def get_base64_preview(self):
        """Generate base64 preview for images"""
        return base64.b64encode(self.file_data).decode('utf-8')
    
class NoteStar(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.ForeignKey(PostNote, related_name='stars', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'note')


class Comment(models.Model):
    note = models.ForeignKey(PostNote, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')
    
    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.note.title}"
    
    def get_vote_count(self):
        return self.votes.filter(vote_type=1).count()
    
class NoteBookmark(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    note = models.ForeignKey(PostNote, related_name='bookmarks', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'note')

    def __str__(self):
        return f"{self.user.username} bookmarked {self.note.title}"


# Add these models to your models.py

class CommentVote(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comment', related_name='votes', on_delete=models.CASCADE)
    vote_type = models.IntegerField(default=1)  # 1 for upvote, -1 for downvote
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"{self.user.username}'s vote on comment {self.comment.id}"

class CommentReport(models.Model):
    REPORT_REASONS = [
        ('spam', 'Spam'),
        ('abuse', 'Abuse/Harassment'),
        ('inappropriate', 'Inappropriate Content'),
        ('other', 'Other')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment = models.ForeignKey('Comment', related_name='reports', on_delete=models.CASCADE)
    reason = models.CharField(max_length=20, choices=REPORT_REASONS)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('reviewed', 'Reviewed'), ('resolved', 'Resolved')],
        default='pending'
    )

    class Meta:
        unique_together = ('user', 'comment')

    def __str__(self):
        return f"Report by {self.user.username} on comment {self.comment.id}"


""" class NoteSummary(models.Model):
    note = models.ForeignKey('PostNote', on_delete=models.CASCADE, related_name='summaries')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='generated_summaries')
    is_latest = models.BooleanField(default=False)
    summary_type = models.CharField(
        max_length=10, 
        choices=[('brief', 'Brief'), ('detailed', 'Detailed')],
        default='brief'
    )

    def save(self, *args, **kwargs):
        # Ensure only one summary is marked as latest
        if self.is_latest:
            NoteSummary.objects.filter(note=self.note, is_latest=True).update(is_latest=False)
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "Note Summaries"

"""


class QuizGeneration(models.Model):
    note = models.ForeignKey(PostNote, on_delete=models.CASCADE, related_name='quizzes')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    quiz_type = models.CharField(max_length=20, choices=[
        ('basic', 'Basic Quiz'),
        ('advanced', 'Advanced Quiz')
    ])
    question_count = models.IntegerField(default=5)
    
    def __str__(self):
        return f"Quiz for {self.note.title} by {self.user.username}"
    
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()

class Notification(models.Model):
    # Notification types as choices
    TYPE_STAR = 'star'
    TYPE_COMMENT = 'comment'
    TYPE_FOLLOWING = 'following'
    TYPE_FOLLOWED = 'followed'
    TYPE_COMMENT_LIKE = 'comment_like'
    TYPE_COMMENT_REPLY = 'comment_reply'
    
    NOTIFICATION_TYPES = (
        (TYPE_STAR, 'Star on Note'),
        (TYPE_COMMENT, 'Comment on Note'),
        (TYPE_FOLLOWING, 'Following'),
        (TYPE_FOLLOWED, 'Followed'),
        (TYPE_COMMENT_LIKE, 'Like on Comment'),
        (TYPE_COMMENT_REPLY, 'Reply to Comment'),
    )
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    note = models.ForeignKey('PostNote', on_delete=models.CASCADE, null=True, blank=True)
    comment = models.ForeignKey('Comment', on_delete=models.CASCADE, null=True, blank=True)
    rank = models.PositiveIntegerField(null=True, blank=True)  # For rank-based notifications
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.message[:50]}"
    
class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followed = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('follower', 'followed')
        
    def __str__(self):
        return f"{self.follower.username} follows {self.followed.username}"