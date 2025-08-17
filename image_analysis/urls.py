from django.urls import path
from . import views
from .api import stories

urlpatterns = [
    # Frontend (root of app)
    path('', views.index_view, name='index'),
    
    # API endpoints
    path('analyze-image/', views.ImageAnalysisView.as_view(), name='analyze-image'),
    path('regenerate-article/', views.RegenerateArticleView.as_view(), name='regenerate-article'),
    
    # New stories endpoints
    path('stories/', stories.StoriesView.as_view(), name='stories'),
    path('stories/<uuid:story_id>/', stories.StoryDetailView.as_view(), name='story-detail'),
    path('stories/<uuid:story_id>/share/', stories.StoryShareView.as_view(), name='story-share'),
]
