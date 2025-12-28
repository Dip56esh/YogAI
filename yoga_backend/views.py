from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .pose_detector import get_detector
from .models import YogaSession, PoseDetection
import logging

from django.db.models import Avg, Sum, Count
from django.db.models.functions import Coalesce
from datetime import timedelta

logger = logging.getLogger(__name__)


class PoseDetectionView(APIView):
    """
    API endpoint to detect yoga pose from a video frame
    
    POST /api/yoga/detect/
    Body: {
        "frame": "base64_encoded_image",
        "target_pose": "tree",  # optional
        "session_id": 123       # optional
    }
    """
    
    def post(self, request):
        try:
            # Get request data
            frame_data = request.data.get('frame')
            target_pose = request.data.get('target_pose')
            session_id = request.data.get('session_id')
            
            if not frame_data:
                return Response(
                    {'error': 'No frame data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get detector and process frame
            detector = get_detector()
            result = detector.process_frame(frame_data)
            
            if not result.get('success'):
                return Response(result, status=status.HTTP_200_OK)
            
            # Check if predicted pose matches target
            if target_pose:
                result['matches_target'] = (
                    result['pose'].lower() == target_pose.lower()
                )
            
            # Save detection to database if session exists
            if session_id:
                try:
                    session = YogaSession.objects.get(id=session_id)
                    session.total_frames += 1
                    if result.get('is_correct'):
                        session.correct_frames += 1
                    session.accuracy = (session.correct_frames / session.total_frames) * 100
                    session.save()
                    
                    # Create detection record
                    PoseDetection.objects.create(
                        session=session,
                        predicted_pose=result['pose'],
                        confidence=result['confidence'],
                        is_correct=result.get('is_correct', False)
                    )
                except YogaSession.DoesNotExist:
                    logger.warning(f"Session {session_id} not found")
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in pose detection: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartSessionView(APIView):
    """
    API endpoint to start a new yoga session
    
    POST /api/yoga/session/start/
    Body: {
        "pose": "tree",
        "user_id": 1  # optional
    }
    """
    
    def post(self, request):
        try:
            pose_name = request.data.get('pose', 'tree')
            user_id = request.data.get('user_id')
            
            # Create new session
            session_data = {
                'pose_name': pose_name,
            }
            
            if user_id:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=user_id)
                    session_data['user'] = user
                except User.DoesNotExist:
                    pass
            
            session = YogaSession.objects.create(**session_data)
            
            return Response({
                'success': True,
                'session_id': session.id,
                'target_pose': pose_name,
                'message': 'Session started successfully',
                'started_at': session.started_at.isoformat()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting session: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EndSessionView(APIView):
    """
    API endpoint to end a yoga session
    
    POST /api/yoga/session/end/
    Body: {
        "session_id": 123
    }
    """
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            
            if not session_id:
                return Response(
                    {'error': 'session_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session = YogaSession.objects.get(id=session_id)
            session.ended_at = timezone.now()
            session.save()
            
            duration = (session.ended_at - session.started_at).total_seconds()
            
            return Response({
                'success': True,
                'session_id': session.id,
                'pose': session.pose_name,
                'duration_seconds': duration,
                'total_frames': session.total_frames,
                'correct_frames': session.correct_frames,
                'accuracy': session.accuracy,
                'message': 'Session ended successfully'
            })
            
        except YogaSession.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Error ending session: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetAvailablePosesView(APIView):
    """
    API endpoint to get list of available yoga poses
    
    GET /api/yoga/poses/
    """
    
    def get(self, request):
        detector = get_detector()
        return Response({
            'poses': detector.pose_classes,
            'count': len(detector.pose_classes)
        })


class SessionHistoryView(APIView):
    """
    API endpoint to get session history
    
    GET /api/yoga/sessions/?user_id=1
    """
    
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            
            sessions = YogaSession.objects.all()
            
            if user_id:
                sessions = sessions.filter(user_id=user_id)
            
            # Get recent sessions
            sessions = sessions[:20]
            
            data = []
            for session in sessions:
                data.append({
                    'id': session.id,
                    'pose': session.pose_name,
                    'started_at': session.started_at.isoformat(),
                    'ended_at': session.ended_at.isoformat() if session.ended_at else None,
                    'total_frames': session.total_frames,
                    'correct_frames': session.correct_frames,
                    'accuracy': session.accuracy
                })
            
            return Response({
                'sessions': data,
                'count': len(data)
            })
            
        except Exception as e:
            logger.error(f"Error getting session history: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
class UserStatsView(APIView):
    """
    API endpoint to get user statistics
    
    GET /api/yoga/user/stats/?user_id=1
    """
    
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            
            # Get all sessions (with or without user_id)
            if user_id:
                sessions = YogaSession.objects.filter(user_id=user_id)
            else:
                # For anonymous users, get all sessions
                sessions = YogaSession.objects.all()
            
            # Filter only completed sessions (those with ended_at)
            completed_sessions = sessions.filter(ended_at__isnull=False)
            
            # Calculate total sessions
            total_sessions = completed_sessions.count()
            
            # Calculate average accuracy
            avg_accuracy = completed_sessions.aggregate(
                avg_acc=Coalesce(Avg('accuracy'), 0.0)
            )['avg_acc']
            
            # Calculate total hours
            total_seconds = 0
            for session in completed_sessions:
                if session.started_at and session.ended_at:
                    duration = (session.ended_at - session.started_at).total_seconds()
                    total_seconds += duration
            
            total_hours = total_seconds / 3600  # Convert to hours
            
            # Calculate longest streak (consecutive days)
            longest_streak = self.calculate_longest_streak(completed_sessions)
            
            # Get recent sessions
            recent_sessions = completed_sessions.order_by('-started_at')[:5]
            recent_sessions_data = []
            for session in recent_sessions:
                duration = (session.ended_at - session.started_at).total_seconds() if session.ended_at else 0
                recent_sessions_data.append({
                    'id': session.id,
                    'pose': session.pose_name,
                    'date': session.started_at.strftime('%Y-%m-%d'),
                    'time': session.started_at.strftime('%H:%M'),
                    'duration': f"{int(duration // 60)}m {int(duration % 60)}s",
                    'accuracy': round(session.accuracy, 1)
                })
            
            return Response({
                'total_sessions': total_sessions,
                'avg_accuracy': round(avg_accuracy, 1),
                'total_hours': round(total_hours, 2),
                'longest_streak': longest_streak,
                'recent_sessions': recent_sessions_data
            })
            
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def calculate_longest_streak(self, sessions):
        """Calculate longest consecutive days streak"""
        if not sessions.exists():
            return 0
        
        # Get unique dates of sessions
        session_dates = set()
        for session in sessions:
            if session.started_at:
                session_dates.add(session.started_at.date())
        
        if not session_dates:
            return 0
        
        sorted_dates = sorted(session_dates)
        longest_streak = 1
        current_streak = 1
        
        for i in range(1, len(sorted_dates)):
            if (sorted_dates[i] - sorted_dates[i-1]).days == 1:
                current_streak += 1
                longest_streak = max(longest_streak, current_streak)
            else:
                current_streak = 1
        
        return longest_streak