# -*- coding: ISO-8859-1 -*-
import json
import datetime
from django.views.generic.base import TemplateView
from django.views.generic.edit import CreateView, UpdateView
from django.db.models import Q
from rest_framework import viewsets

from ...core.base.core_base_datatable import CoreBaseDatatableView
from ...core.mixins.core_mixin_form import CoreMixinForm, CoreMixinDel
from ...core.mixins.core_mixin_login import CoreMixinLoginRequired

from ..models.movimentovisitante import MovimentoVisitante
from ..models.movimentoveiculo import MovimentoVeiculo, MovimentoVeiculoSerializer

from ..forms.visitante_form import MovimentoVisitanteForm
from ..forms.veiculo_form import MovimentoVeiculoForm, MovimentoVeiculoUpdateForm

class MovimentoVeiculoList(CoreMixinLoginRequired, TemplateView):
    """
    View para renderização da lista
    """
    template_name = 'portaria/movimentoveiculo_list.html'
    
class MovimentoVeiculoData(CoreMixinLoginRequired, CoreBaseDatatableView):
    """
    View para renderização da lista
    """
    model = MovimentoVeiculo
    columns = [ 'entrada', 'entrada_hora', 'saida', 'saida_hora', 'codigo', 'veiculo', 'placa', 'nota', 'fornecedor', 'buttons', ]
    order_columns = ['entrada', 'saida', 'codigo', 'placa', 'nota', ]
    max_display_length = 500
    url_base_form = '/portaria/movimento/veiculo/'

    def render_column(self, row, column):
        if column == 'entrada':
            sReturn = row.entrada.strftime('%d/%m/%Y')
            return sReturn
        elif column == 'saida':
            if row.saida:
                sReturn = row.saida.strftime('%d/%m/%Y')
            else:
                sReturn = ''
            return sReturn
        else:
            return super(MovimentoVeiculoData, self).render_column(row, column)
    
    def filter_queryset(self, qs):
        """
        Filtros da query baseado no datatable
        """
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            search_parts = sSearch.split('+')
            qs_params = None
            for part in search_parts:
                try:
                    q = Q(entrada=datetime.datetime.strptime(part, '%d/%m/%Y'))|Q(saida=datetime.datetime.strptime(part, '%d/%m/%Y'))
                except:
                    q = Q(codigo__istartswith=part)|Q(veiculo__istartswith=part) \
                       |Q(placa__istartswith=part)|Q(nota__istartswith=part) \
                       |Q(fornecedor__istartswith=part)

                qs_params = qs_params | q if qs_params else q

            qs = qs.filter(qs_params)

        return qs

class MovimentoVeiculoCreateForm(CoreMixinLoginRequired, CreateView, CoreMixinForm):
    model = MovimentoVeiculo
    template_name = 'portaria/movimentoveiculo_form.html'
    success_url = '/'
    form_class = MovimentoVeiculoForm

    def get_form_kwargs(self):
        kwargs = super(MovimentoVeiculoCreateForm, self).get_form_kwargs()
        if hasattr(self, 'object'):
            if not self.object:
                kwargs.update({
                    'initial': {
                        "entrada": datetime.date.today(),
                        "entrada_hora": datetime.datetime.now().time(),
                    }
                })
            
        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = None

        # pega os ocupantes do carro
        ocupantes = [json.loads(item) for item in request.POST.getlist('ocupantes[]')]

        if not ocupantes:
            return self.render_to_json_reponse(
                context={
                    'success':False, 
                    'message': 'Não foram preenchidos ocupantes para o veículo.'
                },
                status=400
            )

        for ocupante in ocupantes:
            ocupante.update({'motivo': request.POST.get('motivo')})
            print ocupante
            ocupate_form = MovimentoVisitanteForm(ocupante)
            if not ocupate_form.is_valid():
                return self.render_to_json_reponse(
                    context={
                        'success':False, 
                        'message': 'Revise os dados dos ocupantes, alguns estão inconsistentes.'
                    },
                    status=400
                )
             
        form_class = self.get_form_class()
        form = self.get_form(form_class)   
        if form.is_valid():
            return self.form_valid(form, ocupantes)
        else:
            return self.form_invalid(form)

    def form_valid(self, form, ocupantes):
        response = super(MovimentoVeiculoCreateForm, self).form_valid(form)
        dataToLabel = []
        
        for ocupante in ocupantes:
            visitante = MovimentoVisitante(
                cpf = ocupante['cpf'],
                nome = ocupante['nome'],
                empresa = ocupante['empresa'],
                veiculo = self.object,
                liberado_por = self.object.liberado_por,
                obs = self.object.obs,
            )
            visitante.save()
            dataToLabel.append(visitante.pk)

        self.request.session['dataEtiquetaVisitante'] = dataToLabel
        return self.render_to_json_reponse(
            context={
                'success':True, 
                'message': 'Registro salvo com sucesso...'
            },
            status=200
        )

class MovimentoVeiculoUpdateForm(CoreMixinLoginRequired, UpdateView, CoreMixinForm):
    """
    Formulário de criação
    """
    model = MovimentoVeiculo
    template_name = 'portaria/movimentoveiculo_update_form.html'
    success_url = '/'
    form_class = MovimentoVeiculoUpdateForm

    def get_form_kwargs(self):
        kwargs = super(MovimentoVeiculoUpdateForm, self).get_form_kwargs()
        if hasattr(self, 'object'):
            if self.object.entrada:
                kwargs.update({
                    'initial': {
                        "saida": datetime.date.today(),
                        "saida_hora": datetime.datetime.now().time(),
                    }
                })

        return kwargs

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.registerExit():
            for visitante in self.object.ocupantes.all():
                visitante.registerExit()

            return self.render_to_json_reponse(
                context={
                    'success':True, 
                    'message': 'Registro salvo com sucesso...'
                },
                status=200
            )
        else:
            return self.render_to_json_reponse(
                context={
                    'success':False, 
                    'message': 'Não foi possível realizar a saída do veículo'
                },
                status=400
            )

class MovimentoVeiculoDelete(CoreMixinLoginRequired, CoreMixinDel):
    """
    View de exclusão de itens
    """
    model = MovimentoVeiculo
    success_url = '/portaria/movimento/veiculo/'