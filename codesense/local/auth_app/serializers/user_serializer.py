from rest_framework import serializers

class RegisterUserSerializer(serializers.Serializer):
    company = serializers.CharField()
    name = serializers.CharField()
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=['Admin', 'Manager', 'User'])

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
