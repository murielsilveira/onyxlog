# -*- coding: ISO-8859-1 -*-
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Q
from django.shortcuts import redirect
from django.http import Http404

from ...core.base.core_base_datatable import CoreBaseDatatableView
from ...core.mixins.core_mixin_form import CoreMixinForm, CoreMixinDel
from ...core.mixins.core_mixin_login import CoreMixinLoginRequired

from ..models.motivo import Motivo

class MotivoList(CoreMixinLoginRequired, TemplateView):
    """
    View para renderização da lista
    """
    template_name = 'portaria/motivo_list.html'
    
class MotivoData(CoreMixinLoginRequired, CoreBaseDatatableView):
    """
    View para renderização da lista
    """
    model = Motivo
    columns = ['nome', 'buttons', ]
    order_columns = ['nome',]
    max_display_length = 500
    url_base_form = '/portaria/motivo/'
    
    def filter_queryset(self, qs):
        """
        Filtros da query baseado no datatable
        """
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            search_parts = sSearch.split('+')
            qs_params = None
            for part in search_parts:
                q = Q(nome__istartswith=part)
                qs_params = qs_params | q if qs_params else q

            qs = qs.filter(qs_params)

        return qs

class MotivoCreateForm(CoreMixinLoginRequired, CreateView, CoreMixinForm):
    """
    Formulário de criação
    """
    model = Motivo
    template_name = 'portaria/motivo_form.html'
    success_url = '/'

class MotivoUpdateForm(CoreMixinLoginRequired, UpdateView, CoreMixinForm):
    """
    Formulário de criação
    """
    model = Motivo
    template_name = 'portaria/motivo_form.html'
    success_url = '/'

class MotivoDelete(CoreMixinLoginRequired, CoreMixinDel):
    """
    View de exclusão de itens
    """
    model = Motivo
    success_url = '/portaria/motivo/'