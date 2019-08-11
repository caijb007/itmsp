# coding: utf-8
# Author: ld
from django.conf.urls import include, url
from . import views, app_view
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

router.register(r'network', views.NetworkSegmentViewSet)
router.register(r'ipusage', views.IPUsageViewSet)
router.register(r'vmgenerate-approval', app_view.VMGenerateApprovalViewSet)
router.register(r'vmgenerate-approval-ord', app_view.VMGenerateApprovalOrderViewSet)
router.register(r'vmgenerate-approve', app_view.VMGenerateApproveViewSet)
router.register(r'vmgenerate-approve-ord', app_view.VMGenerateApproveOrderViewSet)

urlpatterns = [
    # interface of clould that used vmomi
    url(r'^clould/', include([
        url(r'server/', include([
            url(r'^get-params-http/$', views.get_params_http),
            url(r'^get-datacenter/$', views.get_datacenter),
            url(r'^get-cluster/$', views.get_cluster),
            url(r'^get-cluster-hosts/$', views.get_cluster_hosts),
            url(r'^get-host-network/$', views.get_host_network),
            url(r'^get-host-datastore/$', views.get_host_datastore),
            url(r'^get-templates/$', views.get_templates),
            url(r'^network-recommend/$', views.network_recommend),
            url(r'^ping-ip/$', views.ping_ip),
            url(r'^get-networks/$', views.get_networks),
            url(r'^vc-resource-recommend/$', views.vc_resource_recommend),
            url(r'^prod-virtual-machine/$', views.prod_virtual_machine),
            url(r'^clone-virtual-machine/$', views.clone_virtual_machine),
            url(r'^reconfigure-virtual-machine/$', views.reconfigure_virtual_machine),
            url(r'^poweron-virtual-machine/$', views.poweron_virtual_machine),
            url(r'^poweroff-virtual-machine/$', views.poweroff_virtual_machine),
            url(r'^destroy-virtual-machine/$', views.destroy_virtual_machine),
            url(r'^push-pubkey/$', views.push_pubkey),
            url(r'^get-virtualmachines/$', views.get_virtualmachines),
            url(r'^get-virtualmachine-info/$', views.get_virtualmachine_info),
            url(r'^search-vm-name/$', views.search_vm_name)
        ])),
        url(r'vmomi/', include([
            url(r'^get-cluster-resp/$', views.get_cluster_resp),
            url(r'^get-datacenter-network/$', views.get_datacenter_network),
            url(r'^get-best-hosts/$', views.get_best_hosts),
            url(r'^get-best-datastore/$', views.get_best_datastore),
            url(r'^get-customspec/$', views.get_customspec),
            url(r'^default-vmware-name/$', views.default_vmware_name),
            url(r'^delete-customspec/$', views.delete_customspec),
            url(r'^get-disk/$', views.get_disk),
            url(r'^add-disk/$', views.add_disk),
            url(r'^remove-vg/$', views.remove_vg),
            url(r'^vm-partition/$', views.vm_partition),
            url(r'^vm-add-user/$', views.vm_add_user),
            url(r'^vm-install-soft/$', views.vm_install_soft),
            url(r'^get-vm-by-dnsname/$', views.get_vm_by_dnsname),
            url(r'^get-vm-by-ip/$', views.get_vm_by_ip),
        ]))
    ])),
    url(r'', include(router.urls)),
    url(r'test', views.test)
]
