from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .pose_detector import get_detector
from .models import YogaSession, PoseDetection
import logging

logger = logging.getLogger(__name__)


class PoseDetectionView(APIView):
    """
    API endpoint to detect yoga pose from a video frame
    """
    
    def post(self, request):
        try:
            logger.info("=" * 50)
            logger.info("DETECTION REQUEST RECEIVED")
            
            # Get request data
            frame_data = request.data.get('frame')
            target_pose = request.data.get('target_pose')
            session_id = request.data.get('session_id')
            
            logger.info(f"Target Pose: {target_pose}")
            logger.info(f"Session ID: {session_id}")
            logger.info(f"Frame data length: {len(frame_data) if frame_data else 0}")
            
            if not frame_data:
                logger.error("No frame data provided")
                return Response(
                    {'error': 'No frame data provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get detector and process frame
            logger.info("Getting detector instance...")
            detector = get_detector()
            
            logger.info(f"Processing frame for pose: {target_pose}")
            result = detector.process_frame(frame_data, target_pose)
            
            logger.info(f"Detection result: {result}")
            
            if not result.get('success'):
                logger.warning(f"Detection failed: {result}")
                return Response(result, status=status.HTTP_200_OK)
            
            # Check if predicted pose matches target
            if target_pose:
                result['matches_target'] = (
                    result.get('pose', '').lower() == target_pose.lower()
                )
                logger.info(f"Matches target: {result['matches_target']}")
            
            # Save detection to database if session exists
            if session_id:
                try:
                    session = YogaSession.objects.get(id=session_id)
                    session.total_frames += 1
                    if result.get('is_correct'):
                        session.correct_frames += 1
                    session.accuracy = (session.correct_frames / session.total_frames) * 100
                    session.save()
                    
                    logger.info(f"Updated session {session_id}: {session.correct_frames}/{session.total_frames}")
                    
                    # Create detection record
                    PoseDetection.objects.create(
                        session=session,
                        predicted_pose=result.get('pose', 'unknown'),
                        confidence=result.get('confidence', 0),
                        is_correct=result.get('is_correct', False)
                    )
                except YogaSession.DoesNotExist:
                    logger.warning(f"Session {session_id} not found")
                except Exception as e:
                    logger.error(f"Error updating session: {e}")
            
            logger.info("Returning detection result")
            logger.info("=" * 50)
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"ERROR in pose detection: {e}", exc_info=True)
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StartSessionView(APIView):
    """
    API endpoint to start a new yoga session
    """
    
    def post(self, request):
        try:
            logger.info("=" * 50)
            logger.info("START SESSION REQUEST RECEIVED")
            
            pose_name = request.data.get('pose', 'plank')  # Changed default to plank
            user_id = request.data.get('user_id')
            
            logger.info(f"Starting session for pose: {pose_name}")
            logger.info(f"User ID: {user_id}")
            
            # Create new session
            session_data = {
                'pose_name': pose_name,
            }
            
            if user_id:
                from django.contrib.auth.models import User
                try:
                    user = User.objects.get(id=user_id)
                    session_data['user'] = user
                    logger.info(f"User found: {user.username}")
                except User.DoesNotExist:
                    logger.warning(f"User {user_id} not found")
            
            session = YogaSession.objects.create(**session_data)
            
            logger.info(f"Session created with ID: {session.id}")
            logger.info("=" * 50)
            
            return Response({
                'success': True,
                'session_id': session.id,
                'target_pose': pose_name,
                'message': 'Session started successfully',
                'started_at': session.started_at.isoformat()
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Error starting session: {e}", exc_info=True)
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class EndSessionView(APIView):
    """
    API endpoint to end a yoga session
    """
    
    def post(self, request):
        try:
            session_id = request.data.get('session_id')
            
            logger.info(f"Ending session: {session_id}")
            
            if not session_id:
                return Response(
                    {'error': 'session_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            session = YogaSession.objects.get(id=session_id)
            session.ended_at = timezone.now()
            session.save()
            
            duration = (session.ended_at - session.started_at).total_seconds()
            
            logger.info(f"Session {session_id} ended. Duration: {duration}s")
            
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
            logger.error(f"Error ending session: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GetAvailablePosesView(APIView):
    """
    API endpoint to get list of available yoga poses
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