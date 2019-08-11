# coding: utf-8
# Author: Dunkle Qiu

from traceback import format_exc
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from iuser.permissions import *
from itmsp.utils.decorators import post_validated_fields, status, post_data_to_dict
from itmsp.utils.base import logger, split, smart_get
from itmsp.utils.pinyin import PinYin

from .serializers import ExUserSerializer
from .utils import *


@api_view(['POST'])
@permission_classes((require_menu(["I00301"]),))
def ajax_user_list(request):
    """
    ajax请求 - 动态搜索 - 用户列表
    * 参数
    ** search  - 搜索
    ** limit - 返回记录条数
    """
    req_dict = post_data_to_dict(request.data)
    PYWorker = PinYin()
    search = smart_get(req_dict, 'search', unicode)
    limit = smart_get(req_dict, 'limit', int)
    try:
        result = []
        q_set = ExUser.objects.all()
        if search:
            search = search.lower()
            for q in q_set:
                if search in q.username.lower() \
                        or search in q.name.lower() \
                        or search in PYWorker.hanzi2pinyin_split(q.name) \
                        or search in PYWorker.hanzi2firstletter(q.name):
                    result.append(q)
        else:
            result = q_set
        serializer = ExUserSerializer(result[:limit], many=True)
    except Exception, e:
        msg = u"失败, 错误信息: " + unicode(e)
        logger.error(format_exc())
        return Response({"status": -1, "msg": msg, "data": {}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        msg = u"成功!"
        return Response({"status": 0, "msg": msg, "data": serializer.data})
