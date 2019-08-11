# coding: utf-8
# Author: ld
from collections import defaultdict
from .models import *


def build_graph(nodes):
    """
    将节点nodes使用邻接字典表示图
    参数
    ** nodes, 所有蓝图节点, [obj]
    返回值
    *** graph， 图, dict
    """
    graph = defaultdict(list)
    last_node = list()

    for node in nodes:
        down_nodes = node.downstream_node.all()

        for d_node in down_nodes:
            graph[node.id].append(d_node.id)

        # python列表为空不执行语句， 传递空列表
        if not len(down_nodes):
            graph[node.id] = list()
            last_node.append(graph[node.id])
            if len(last_node) > 1:
                raise Exception(u"结束节点唯一, 请修改后保存")
    return graph


def topo_sort(graph):
    """
    图graph拓扑排序
    参数
    ** graph, 需排序的图, dict
    返回值
    *** 成功返回排序后的列表
    *** 存在环返回False
    """
    # 初始化所有顶点入度为0
    in_degrees = dict((u, 0) for u in graph)
    vertex_num = len(in_degrees)
    for u in graph:
        for v in graph[u]:
            # 计算每个顶点的入度
            in_degrees[v] += 1

    # 筛选入度为0的顶点
    Q = [u for u in in_degrees if in_degrees[u] == 0]
    result = list()

    while Q:
        u = Q.pop()
        result.append(u)
        for v in graph[u]:
            in_degrees[v] -= 1
            if in_degrees[v] == 0:
                Q.append(v)

    # 若不相等，则存在环
    if len(result) == vertex_num:
        return result
    else:
        return False


def is_valid_params(target_nodes):
    """
    验证蓝图节点参数是否完整
    参数
    ** target_nodes, 所有节点, [obj]
    """
    for target_node in target_nodes:
        target_params = target_node.component_data.get('params')
        for target_param in target_params:
            target_param_name = target_param.get('param_name')
            # 必填项合输入项
            require = target_param.get('require') and target_param.get('io_stream') == "输入"
            target_param_type = target_param.get('data_type')
            if require:
                node_map_set = BlueNodeMapParam.objects.filter(blue_print=target_node.blue_print,
                                                               target_node=target_node.id,
                                                               target_param_name=target_param_name)
                if not len(node_map_set):
                    target_node.is_verify = False
                    raise Exception(u"%s 节点缺少必填输入项" % target_node)
                else:
                    node_map = node_map_set[0]
                    source_node = BlueNodeDefinition.objects.get(id=node_map.source_node)
                    source_param_name = node_map.source_param_name

                    source_param_type = None
                    source_params = source_node.component_data.get('params')
                    for source_param in source_params:
                        if source_param['param_name'] == source_param_name:
                            source_param_type = source_param.get('data_type')
                            break

                    if target_param_type != source_param_type:
                        target_node.is_verify = False
                        raise Exception(u"%s节点参数%s,数据类型应为 %s" % (target_node, target_param_name, target_param_type))

        target_node.is_verify = True
        target_node.save()
