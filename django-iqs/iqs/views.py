from django.db.models import F, Q
from django.forms.models import model_to_dict
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone
from django.views import generic

from .models import GeoLayer, Attribute


# Class based views
class IndexView(generic.ListView):
    model = GeoLayer # todo: remove
    template_name = "iqs/index.html"


class GeolayerView(generic.ListView):
    model = GeoLayer 
    template_name = "iqs/geolayer.html"
    context_object_name = "geolayers"


class GeolayerDetailView(generic.DetailView):
    model = GeoLayer
    template_name = "iqs/geolayer_detail.html"
    context_object_name = "geolayer"


class AttributeView(generic.ListView):
    model = Attribute
    template_name = "iqs/attribute.html"
    context_object_name = "attributes"

    def get_queryset(self):
        # Get the layer ID from the URL
        geolayer_pk = self.kwargs['pk']
        # Optionally: validate that the layer exists
        self.geolayer = get_object_or_404(GeoLayer, pk=geolayer_pk)
        # Return only attributes related to this layer

        return Attribute.objects.filter(geolayer=self.geolayer)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['geolayer'] = self.geolayer  # Pass the geolayer to the template

        return context


class AttributeDetailView(generic.DetailView):
    model_ = Attribute
    template_name = "iqs/attribute_detail.html"
    context_object_name = "attribute"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Converts the model instance to a dict: {'name': 'X', 'value': 'Y', ...}
        context['fields'] = model_to_dict(self.object)
        context['fields']['geolayer'] = self.object.geolayer
        context['fields']['type'] = self.object.type
    
        return context
    
    def get_object(self, queryset=None):
        return get_object_or_404(
            Attribute,
            pk=self.kwargs['attribute_pk'],
            geolayer__pk=self.kwargs['geolayer_pk']
        )
