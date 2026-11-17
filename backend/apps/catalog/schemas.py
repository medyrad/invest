"""Versioned DTO validation shared by the future forms and this stateless endpoint."""

from rest_framework import serializers

from .values import normalize


class ValueInputSerializer(serializers.BaseSerializer):
    def to_internal_value(self, data):
        return normalize(data)

    def to_representation(self, instance):
        return instance
