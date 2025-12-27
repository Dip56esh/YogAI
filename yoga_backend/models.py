from django.db import models
from django.contrib.auth.models import User


class YogaSession(models.Model):
    """Model to track yoga sessions"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    pose_name = models.CharField(max_length=100)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    total_frames = models.IntegerField(default=0)
    correct_frames = models.IntegerField(default=0)
    accuracy = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['-started_at']
    
    def __str__(self):
        return f"{self.pose_name} - {self.started_at}"


class PoseDetection(models.Model):
    """Model to store individual pose detections"""
    session = models.ForeignKey(YogaSession, on_delete=models.CASCADE, related_name='detections')
    timestamp = models.DateTimeField(auto_now_add=True)
    predicted_pose = models.CharField(max_length=100)
    confidence = models.FloatField()
    is_correct = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.predicted_pose} - {self.confidence:.2f}"