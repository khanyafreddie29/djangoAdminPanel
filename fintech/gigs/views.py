from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters import rest_framework as filters
from .models import Gig
from .serializers import GigSerializer, GigListSerializer
from adminPanel.permissions import IsAdminOrSuperAdmin
from adminPanel.models import AdminAction
from adminPanel.utils import get_client_ip
from notifications.tasks import queue_email


class GigFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Gig.STATUS_CHOICES)
    category = filters.ChoiceFilter(choices=Gig.CATEGORY_CHOICES)
    min_budget = filters.NumberFilter(field_name='budget', lookup_expr='gte')
    max_budget = filters.NumberFilter(field_name='budget', lookup_expr='lte')
    title = filters.CharFilter(lookup_expr='icontains')
    location = filters.CharFilter(lookup_expr='icontains')

    class Meta:
        model = Gig
        fields = ['status', 'category', 'client', 'hustler']


class GigViewSet(viewsets.ModelViewSet):
    filterset_class = GigFilter
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_serializer_class(self):
        if self.action == 'list':
            return GigListSerializer
        return GigSerializer

    def get_permissions(self):
        if self.action in ('update', 'partial_update'):
            return [IsAdminOrSuperAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.user_type == 'client':
            return Gig.objects.filter(client=user)
        if user.user_type == 'hustler':
            return Gig.objects.filter(hustler=user) | Gig.objects.filter(status='open')
        return Gig.objects.all()

    def perform_create(self, serializer):
        gig = serializer.save(client=self.request.user, status='open')
        queue_email(
            user_id=self.request.user.id,
            event_type='gig_created',
            context_data={
                'gig_id': gig.id,
                'title': gig.title,
                'budget': str(gig.budget),
                'location': gig.location,
                'status': gig.status,
            }
        )

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Gigs cannot be deleted.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['patch'])
    def accept(self, request, pk=None):
        """Hustler accepts an open gig."""
        gig = self.get_object()

        if request.user.user_type != 'hustler':
            return Response(
                {'error': 'Only hustlers can accept gigs.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if gig.status != 'open':
            return Response(
                {'error': 'Only open gigs can be accepted.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        gig.hustler = request.user
        gig.status = 'accepted'
        gig.save()

        return Response({
            'status': 'Gig accepted.',
            'gig_id': gig.id,
            'new_status': gig.status,
        })

    @action(detail=True, methods=['patch'])
    def start(self, request, pk=None):
        """Hustler marks an accepted gig as in progress."""
        gig = self.get_object()

        if request.user != gig.hustler:
            return Response(
                {'error': 'Only the assigned hustler can start this gig.'},
                status=status.HTTP_403_FORBIDDEN
            )
        if gig.status != 'accepted':
            return Response(
                {'error': 'Only accepted gigs can be started.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        gig.status = 'in_progress'
        gig.save(update_fields=['status', 'updated_at'])

        return Response({
            'status': 'Gig is now in progress.',
            'gig_id': gig.id,
            'new_status': gig.status,
        })

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Client only — update their own gig status."""
        gig = self.get_object()

        if request.user != gig.client:
            return Response(
                {'error': 'Only the client can update this gig status.'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        valid_statuses = dict(Gig.STATUS_CHOICES).keys()
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Choices are: {list(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        gig.status = new_status
        gig.save(update_fields=['status', 'updated_at'])

        return Response({
            'status': f'Gig updated to {new_status}',
            'gig_id': gig.id,
        })

    @action(detail=True, methods=['patch'])
    def confirm(self, request, pk=None):
        """Client or hustler confirms completion."""
        gig = self.get_object()
        user = request.user

        if gig.status != 'pending_confirmation':
            return Response(
                {'error': 'Gig must be in pending_confirmation status.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user == gig.client:
            gig.client_confirmed = True
        elif user == gig.hustler:
            gig.hustler_confirmed = True
        else:
            return Response(
                {'error': 'Only the client or hustler can confirm this gig.'},
                status=status.HTTP_403_FORBIDDEN
            )

        if gig.client_confirmed and gig.hustler_confirmed:
            gig.status = 'completed'

        gig.save()

        return Response({
            'status': 'Confirmation recorded.',
            'client_confirmed': gig.client_confirmed,
            'hustler_confirmed': gig.hustler_confirmed,
            'gig_status': gig.status,
        })