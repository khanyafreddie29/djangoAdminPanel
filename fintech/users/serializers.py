# users/serializers.py
from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'user_type', 'is_active', 'is_verified', 'created_at']
        read_only_fields = ['created_at', 'is_active']


class UserDetailSerializer(serializers.ModelSerializer):
    """Detailed user serializer"""
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'user_type', 'phone_number', 'is_active', 'is_verified',
            'email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'is_active',
            'is_verified', 'email_verified', 'user_type'
        ]


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Registration serializer — always hashes password correctly"""
    password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name',
            'phone_number', 'user_type', 'password', 'confirm_password'
        ]
        read_only_fields = ['id']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )
        return data

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user