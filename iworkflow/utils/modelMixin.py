# coding:utf-8
# Author: Chery-Huo
from rest_framework.views import APIView
from rest_framework.response import Response


################################通过混合类继承######################

class GenericAPIView(APIView):
    queryset = None
    serializer_class = None

    def get_queryset(self):
        return self.queryset

    def get_serializer(self, *args, **kwargs):
        return self.serializer_class(*args, **kwargs)


class ListModelMixin(object):
    """
    展示操作
    """

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        print queryset
        ser_obj = self.get_serializer(queryset, many=True ,context={'request':request})
        # print ser_obj
        return Response(ser_obj.data)


class CreateModelMixin(object):
    """
    创建操作
    """

    def create(self, request,*args, **kwargs):
        ser_obj = self.get_serializer(data=request.data,context={'request':request})
        if ser_obj.is_valid():
            ser_obj.save()
            return Response(ser_obj.data)
        return Response(ser_obj.errors)


class RetrieveModelMixin(object):
    def retrieve(self, request, pk,*args, **kwargs):
        # 参数对象
        obj = self.get_queryset().filter(pk=pk).first()
        ser_obj = self.get_serializer(obj,context={'request':request})
        return Response(ser_obj.data)


class UpdateModelMixin(object):
    """
    更新操作
    """

    def update(self, request, pk,*args, **kwargs):
        p_obj = self.get_queryset().filter(pk=pk).first()
        ser_obj = self.get_serializer(instance=p_obj, data=request.data, partial=True,context={'request':request})
        if ser_obj.is_valid():
            ser_obj.save()
            return Response(ser_obj.data)
        return Response(ser_obj.errors)


# class DestroyModelMixin(object):
#     """
#     销毁操作
#     """
#
#     def destory(self, request, pk):
#         obj = self.get_queryset().filter(pk=pk).first()
#         if obj:
#             obj.delete()
#             return Response("")
#         return Exception("删除的对象不存在")



class DestroyModelMixin(object):
    """
    Destroy a model instance.
    """
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def perform_destroy(self, instance):
        instance.delete()

from rest_framework.viewsets import ViewSetMixin


class ModelViewSet(ViewSetMixin, GenericAPIView, ListModelMixin, CreateModelMixin, UpdateModelMixin, RetrieveModelMixin,
                   DestroyModelMixin):
    """
    此类仅仅用于继承
    """
    def get_serializer_context(self):
        # print "123"
        # context = super()
        return {'request':self.request}
