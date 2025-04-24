from django import forms
from .models import PostNote, PostFile
from django_summernote.widgets import SummernoteWidget

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs']['accept'] = '.pdf,.doc,.docx,.ppt,.pptx,.jpg,.jpeg,.png,.gif'
        return context

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            max_size = 10 * 1024 * 1024  # 10MB in bytes
            for file in data:
                if file.size > max_size:
                    raise forms.ValidationError(f"File {file.name} is too large. Maximum size is 10MB.")
            result = [single_file_clean(d, initial) for d in data]
        else:
            result = [single_file_clean(data, initial)]
        return result

class NoteForm(forms.ModelForm):
    main_content = forms.CharField(
        required=False,
        widget=SummernoteWidget(attrs={
            'summernote': {
                'placeholder': 'Write your detailed content here...',
            }
        })
    )


    class Meta:
        model = PostNote
        fields = ['title', 'category', 'other_category', 'description', 'main_content', 'tags', 'is_public']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter a compelling title for your notes',
                'maxlength': '200',
                'required': True
            }),
            'category': forms.Select(attrs={
                'class': 'form-select mb-2',
                'required': True,
                'style' : 'font-size: 13px;'
            }),
            'other_category': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Please specify your category',
                'style': 'display: none;',
                'maxlength': '50'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'What will others learn from your notes?',
                'required': True,
                'minlength': '50'
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Separate tags with commas (e.g., math, calculus, derivatives)',
                'pattern': '^[a-zA-Z0-9, ]+$'
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    files = MultipleFileField(
        required=False,
        widget=MultipleFileInput(attrs={
            'class': 'form-control',
            'multiple': True
        })
    )

    def clean_tags(self):
        tags = self.cleaned_data.get('tags')
        if tags:
            tag_list = [tag.strip() for tag in tags.split(',')]
            tag_list = [tag for tag in tag_list if tag][:5]
            return ','.join(tag_list)
        return tags

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        other_category = cleaned_data.get('other_category')
        
        if category == 'other' and not other_category:
            raise forms.ValidationError({
                'other_category': 'Please specify a category when selecting "Other"'
            })
        
        # Clear other_category if not needed
        if category != 'other':
            cleaned_data['other_category'] = ''
            
        return cleaned_data