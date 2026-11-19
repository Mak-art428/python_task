from rest_framework import serializers
from .models import Customer
from django.contrib.auth.models import User


class CustomerSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = Customer
        fields = [
            'id',
            'name',
            'email',
            'phone_number',
            'address',
            'password',
            'confirm_password',
            'created_at',
            'updated_at'
        ]

        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError(
                {'confirm_password': 'Passwords do not match.'}
            )

        return data

    def create(self, validated_data):

        validated_data.pop('confirm_password')
        password = validated_data.pop('password')

        user = User.objects.create_user(
            username=validated_data['email'],
            email=validated_data['email'],
            password=password
        )

        customer = Customer.objects.create(
            user=user,
            **validated_data
        )

        return customer