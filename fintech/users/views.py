# users/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters import rest_framework as filters
from rest_framework.parsers import JSONParser
from .models import User
from .serializers import UserSerializer, UserDetailSerializer, UserRegistrationSerializer
from adminPanel.permissions import (
    IsAdminOrSuperAdmin,
    IsAdminSupportOrAbove,
    IsOwnerOrAdminAbove,
)
from adminPanel.models import AdminAction
from adminPanel.utils import get_client_ip
from notifications.tasks import queue_email


class UserFilter(filters.FilterSet):
    email = filters.CharFilter(lookup_expr='icontains')
    username = filters.CharFilter(lookup_expr='icontains')
    user_type = filters.ChoiceFilter(choices=User.USER_TYPE_CHOICES)
    is_verified = filters.BooleanFilter()
    is_active = filters.BooleanFilter()

    class Meta:
        model = User
        fields = ['email', 'username', 'user_type', 'is_verified', 'is_active']


class UserRegistrationViewSet(viewsets.GenericViewSet):
    """Public registration endpoint. No authentication required."""
    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Trigger terms accepted email on registration
            queue_email(
                user_id=user.id,
                event_type='terms_accepted',
                context_data={
                    'username': user.username,
                    'email': user.email,
                }
            )
            return Response(
                {'status': 'account created successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """
    User management viewset.
    - Admin/super_admin: full access
    - Support: list + retrieve only
    - Customer/merchant: own data only
    """
    serializer_class = UserSerializer
    filterset_class = UserFilter
    http_method_names = ['get', 'post', 'patch', 'head', 'options']

    def get_queryset(self):
        if self.action == 'activate':
            return User.all_objects.all()
        user = self.request.user
        if user.user_type in ('client', 'hustler'):
            return User.objects.filter(id=user.id)
        return User.objects.all()

    def get_permissions(self):
        if self.action in ('suspend', 'activate', 'verify'):
            return [IsAdminOrSuperAdmin()]
        return [IsAuthenticated()]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer

    def get_object(self):
        obj = super().get_object()
        if self.action == 'retrieve' and self.request.user.user_type in ('customer', 'merchant'):
            self.check_object_permissions(self.request, obj)
        return obj

    def check_object_permissions(self, request, obj):
        IsOwnerOrAdminAbove().has_object_permission(request, self, obj)

    def destroy(self, request, *args, **kwargs):
        return Response(
            {'error': 'Users cannot be deleted. Use the suspend action instead.'},
            status=status.HTTP_405_METHOD_NOT_ALLOWED
        )

    @action(detail=True, methods=['post'])
    def suspend(self, request, pk=None):
        user = self.get_object()

        if not user.is_active:
            return Response(
                {'error': 'User is already suspended.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        if user == request.user:
            return Response(
                {'error': 'You cannot suspend yourself.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.suspend()

        AdminAction.objects.create(
            admin=request.user,
            action_type='user_suspend',
            description=f'Suspended user {user.username}',
            ip_address=get_client_ip(request),
            target_user=user,
        )

        return Response({'status': 'user suspended', 'user_id': user.id})

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()

        if user.is_active:
            return Response(
                {'error': 'User is already active.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.activate()

        AdminAction.objects.create(
            admin=request.user,
            action_type='user_activate',
            description=f'Activated user {user.username}',
            ip_address=get_client_ip(request),
            target_user=user,
        )

        return Response({'status': 'user activated', 'user_id': user.id})

    @action(detail=True, methods=['post'])
    def verify(self, request, pk=None):
        user = self.get_object()

        if user.is_verified:
            return Response(
                {'error': 'User is already verified.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.is_verified = True
        user.save(update_fields=['is_verified'])

        AdminAction.objects.create(
            admin=request.user,
            action_type='user_verify',
            description=f'Verified user {user.username}',
            ip_address=get_client_ip(request),
            target_user=user,
        )

        # Trigger payment received email on verification
        queue_email(
            user_id=user.id,
            event_type='account_verified',
            context_data={
                'username': user.username,
                'email': user.email,
            }
        )

        return Response({'status': 'user verified', 'user_id': user.id})

    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        """Get or update the currently authenticated user's own profile."""
        user = request.user

        if request.method == 'GET':
            serializer = UserDetailSerializer(user)
            return Response(serializer.data)

        serializer = UserDetailSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)