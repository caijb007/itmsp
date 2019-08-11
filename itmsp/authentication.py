# coding: utf-8
# Author: Dunkle Qiu

from django.utils import timezone
from django.core.cache import cache
from rest_framework.authentication import TokenAuthentication, exceptions
from rest_framework.authtoken.models import Token

from itmsp.settings import TOKEN_TMOUT
# from opsap.utils.base import logger
from iuser.models import ExUser

TIMEOUT = 10 ** 8


class CacheTokenAuthentication(TokenAuthentication):
    """
    Token认证类, 先从Cache查找Token进行认证
    """

    def authenticate_credentials(self, key):
        cache_key = "username:token:%s" % key
        username = cache.get(cache_key)
        if username is not None:
            # Case 1 - 从缓存正常查找Token
            if TOKEN_TMOUT > 0:
                cache.expire(cache_key, TOKEN_TMOUT)
            user = ExUser.objects.get(username=username)
            return user, None
        elif TOKEN_TMOUT > 0:
            # Case 2 - Token有生命周期且已经过期
            raise exceptions.AuthenticationFailed('Invalid token.')
        else:
            # Case 3 - Token无生命周期, 从DB直接查找(引用框架)
            ret = super(CacheTokenAuthentication, self).authenticate_credentials(key)
            cache.set(cache_key, ret[0].username, timeout=TIMEOUT)
            return ret


def obtain_token(user):
    """
    生成/获取Token, 并保存至Cache中
    """
    token, created = Token.objects.get_or_create(user=user)
    if not created and TOKEN_TMOUT > 0:
        token_life = timezone.now() - token.created
        if token_life.total_seconds() > TOKEN_TMOUT:
            token.delete()
            token = Token.objects.create(user=user)
    # 缓存处理
    cache_key = "username:token:%s" % token.key
    cache.set(cache_key, str(user.username), TIMEOUT)
    if TOKEN_TMOUT > 0:
        cache.expire(cache_key, TOKEN_TMOUT)
    return token
