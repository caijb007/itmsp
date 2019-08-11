# coding: utf-8
# Author: Dunkle Qiu

from rest_framework import serializers

from itmsp.utils.ssh import get_rsakey_from_string, get_key_string

from .models import ExUser, ExGroup


class ExUserSerializerSet(serializers.HyperlinkedModelSerializer):
    groups = serializers.HyperlinkedIdentityField(
        view_name="exgroup-detail",
        lookup_field="pk",
        many=True,
        read_only=True
    )

    class Meta:
        model = ExUser
        fields = ('id', 'username', 'aam_id', 'email', 'is_active', 'name', 'role', 'last_login', 'groups')


class ExUserSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField('name', many=True, read_only=True)

    class Meta:
        model = ExUser
        fields = ('id', 'username', 'aam_id', 'email', 'is_active', 'name', 'role', 'last_login', 'groups')


class ExUserDetailSerializerSet(serializers.HyperlinkedModelSerializer):
    group = serializers.HyperlinkedIdentityField(
        view_name="exgroup-detail",
        lookup_field="pk",
        many=True,
        read_only=True
    )

    mana_group_set = serializers.SlugRelatedField('name', many=True, read_only=True)

    class Meta:
        model = ExUser
        fields = ('id', 'username', 'aam_id', 'email', 'is_active', 'name', 'role', 'last_login',
                  'ssh_pubkey_str', 'ssh_key_expiration', 'groups', 'mana_group_set')


class ExUserDetailSerializer(serializers.ModelSerializer):
    groups = serializers.SlugRelatedField('name', many=True, read_only=True)
    mana_group_set = serializers.SlugRelatedField('name', many=True, read_only=True)

    class Meta:
        model = ExUser
        fields = ('id', 'username', 'aam_id', 'email', 'is_active', 'name', 'role', 'last_login',
                  'ssh_pubkey_str', 'ssh_key_expiration', 'groups', 'mana_group_set')


class ExGroupSerializerSet(serializers.HyperlinkedModelSerializer):
    user_set = serializers.HyperlinkedIdentityField(
        view_name="exuser-detail",
        lookup_field="pk",
        read_only=True,
        many=True
    )
    managers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    menu = serializers.JSONField()

    class Meta:
        model = ExGroup
        fields = ('id', 'name', 'comment', 'member_type', 'user_set', 'managers', 'menu')


class ExGroupSerializer(serializers.ModelSerializer):
    user_set = ExUserSerializer(many=True, read_only=True)
    managers = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    menu = serializers.JSONField()

    class Meta:
        model = ExGroup
        fields = ('id', 'name', 'comment', 'member_type', 'user_set', 'managers', 'menu')
