"""
Newsletter API Views
RESTful API endpoints for newsletter functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from .models import Subscriber, Campaign, EmailLog, ClickTracking
from .serializers import (
    SubscriberSerializer, SubscribeSerializer, CampaignSerializer,
    CampaignCreateUpdateSerializer
)


class SubscriberViewSet(viewsets.ModelViewSet):
    """ViewSet for managing newsletter subscribers."""
    
    serializer_class = SubscriberSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return subscribers based on user permissions."""
        if self.request.user.is_staff:
            return Subscriber.objects.all()
        elif self.request.user.is_authenticated:
            # Users can only see their own subscription
            return Subscriber.objects.filter(user=self.request.user)
        return Subscriber.objects.none()
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get subscriber statistics (staff only)."""
        if not request.user.is_staff:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        total_subscribers = Subscriber.objects.count()
        active_subscribers = Subscriber.objects.active().count()
        verified_subscribers = Subscriber.objects.filter(email_verified=True).count()
        
        # Frequency breakdown
        frequency_stats = {}
        for freq_choice in Subscriber.Frequency.choices:
            freq_code = freq_choice[0]
            count = Subscriber.objects.active().filter(frequency=freq_code).count()
            frequency_stats[freq_code] = count
        
        return Response({
            'total_subscribers': total_subscribers,
            'active_subscribers': active_subscribers,
            'verified_subscribers': verified_subscribers,
            'frequency_breakdown': frequency_stats
        })


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for managing newsletter campaigns."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return campaigns based on user permissions."""
        if self.request.user.is_staff:
            return Campaign.objects.all()
        return Campaign.objects.none()
    
    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ['create', 'update', 'partial_update']:
            return CampaignCreateUpdateSerializer
        return CampaignSerializer
    
    def perform_create(self, serializer):
        """Set creator when creating campaign."""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def send_test(self, request, pk=None):
        """Send test email for campaign."""
        campaign = self.get_object()
        test_email = request.data.get('email')
        
        if not test_email:
            return Response({'error': 'Email address required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Here you would implement the actual email sending logic
        # For now, just return success
        return Response({'message': f'Test email sent to {test_email}'})
    
    @action(detail=True, methods=['post'])
    def schedule(self, request, pk=None):
        """Schedule campaign for sending."""
        campaign = self.get_object()
        scheduled_at = request.data.get('scheduled_at')
        
        if not scheduled_at:
            return Response({'error': 'Scheduled time required'}, status=status.HTTP_400_BAD_REQUEST)
        
        campaign.scheduled_at = scheduled_at
        campaign.status = Campaign.Status.SCHEDULED
        campaign.save()
        
        return Response({'message': 'Campaign scheduled successfully'})
    
    @action(detail=True, methods=['post'])
    def send_now(self, request, pk=None):
        """Send campaign immediately."""
        campaign = self.get_object()
        
        if campaign.status != Campaign.Status.DRAFT:
            return Response(
                {'error': 'Only draft campaigns can be sent'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get target subscribers
        subscribers = campaign.get_target_subscribers()
        campaign.total_recipients = subscribers.count()
        campaign.status = Campaign.Status.SENDING
        campaign.save()
        
        # Here you would queue the emails for sending
        # For now, just update the status
        campaign.status = Campaign.Status.SENT
        campaign.sent_at = timezone.now()
        campaign.emails_sent = campaign.total_recipients
        campaign.save()
        
        return Response({'message': f'Campaign sent to {campaign.total_recipients} subscribers'})
    
    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get campaign statistics."""
        campaign = self.get_object()
        
        return Response({
            'total_recipients': campaign.total_recipients,
            'emails_sent': campaign.emails_sent,
            'emails_delivered': campaign.emails_delivered,
            'emails_opened': campaign.emails_opened,
            'emails_clicked': campaign.emails_clicked,
            'emails_bounced': campaign.emails_bounced,
            'emails_unsubscribed': campaign.emails_unsubscribed,
            'open_rate': round(campaign.open_rate, 2),
            'click_rate': round(campaign.click_rate, 2),
            'bounce_rate': round(campaign.bounce_rate, 2)
        })


class SubscribeView(APIView):
    """Subscribe to newsletter."""
    
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Subscribe user to newsletter."""
        serializer = SubscribeSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            # Check if already subscribed
            try:
                subscriber = Subscriber.objects.get(email=email)
                if subscriber.is_active:
                    return Response(
                        {'message': 'Already subscribed'}, 
                        status=status.HTTP_200_OK
                    )
                else:
                    # Reactivate subscription
                    subscriber.resubscribe()
                    return Response({'message': 'Subscription reactivated'})
            except Subscriber.DoesNotExist:
                # Create new subscription
                # Get client IP
                x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
                if x_forwarded_for:
                    ip = x_forwarded_for.split(',')[0]
                else:
                    ip = request.META.get('REMOTE_ADDR')
                
                subscriber = Subscriber.objects.create(
                    email=email,
                    user=request.user if request.user.is_authenticated else None,
                    frequency=serializer.validated_data.get('frequency', Subscriber.Frequency.WEEKLY),
                    ip_address=ip,
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    source=serializer.validated_data.get('source', 'api')
                )
                
                # Here you would send verification email
                return Response(
                    {'message': 'Subscribed successfully. Please check your email for verification.'}, 
                    status=status.HTTP_201_CREATED
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UnsubscribeView(APIView):
    """Unsubscribe from newsletter."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """Show unsubscribe confirmation page."""
        try:
            subscriber = Subscriber.objects.get(unsubscribe_token=token)
            return Response({
                'email': subscriber.email,
                'is_active': subscriber.is_active
            })
        except Subscriber.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)
    
    def post(self, request, token):
        """Unsubscribe user."""
        try:
            subscriber = Subscriber.objects.get(unsubscribe_token=token)
            reason = request.data.get('reason', '')
            
            subscriber.unsubscribe(reason=reason)
            
            return Response({'message': 'Successfully unsubscribed'})
        except Subscriber.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)


class VerifyEmailView(APIView):
    """Verify email subscription."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, token):
        """Verify email with token."""
        try:
            subscriber = Subscriber.objects.get(verification_token=token)
            
            if subscriber.email_verified:
                return Response({'message': 'Email already verified'})
            
            subscriber.verify_email()
            return Response({'message': 'Email verified successfully'})
        except Subscriber.DoesNotExist:
            return Response({'error': 'Invalid token'}, status=status.HTTP_404_NOT_FOUND)


class TrackOpenView(APIView):
    """Track email opens."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, tracking_id):
        """Track email open with tracking pixel."""
        try:
            email_log = EmailLog.objects.get(tracking_id=tracking_id)
            
            if email_log.status == EmailLog.Status.DELIVERED:
                email_log.status = EmailLog.Status.OPENED
                email_log.opened_at = timezone.now()
                email_log.save()
                
                # Update campaign stats
                campaign = email_log.campaign
                campaign.emails_opened += 1
                campaign.save()
            
            # Return 1x1 transparent pixel
            pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
            return HttpResponse(pixel_data, content_type='image/gif')
        except EmailLog.DoesNotExist:
            # Return pixel anyway to avoid broken images
            pixel_data = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x04\x01\x00\x3b'
            return HttpResponse(pixel_data, content_type='image/gif')


class TrackClickView(APIView):
    """Track email clicks."""
    
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, tracking_id):
        """Track email click and redirect."""
        url = request.GET.get('url')
        if not url:
            return Response({'error': 'URL parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_log = EmailLog.objects.get(tracking_id=tracking_id)
            
            # Track the click
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0]
            else:
                ip = request.META.get('REMOTE_ADDR')
            
            ClickTracking.objects.create(
                email_log=email_log,
                url=url,
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            # Update email log status
            if email_log.status in [EmailLog.Status.DELIVERED, EmailLog.Status.OPENED]:
                email_log.status = EmailLog.Status.CLICKED
                email_log.clicked_at = timezone.now()
                email_log.save()
                
                # Update campaign stats
                campaign = email_log.campaign
                campaign.emails_clicked += 1
                campaign.save()
            
            # Redirect to the actual URL
            from django.shortcuts import redirect
            return redirect(url)
        except EmailLog.DoesNotExist:
            # Redirect anyway
            from django.shortcuts import redirect
            return redirect(url)