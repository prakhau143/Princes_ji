from django import forms
from .models import Collection, CollectionRow, ZoomCarouselItem, Product
import json


class CollectionForm(forms.ModelForm):
	"""Form for creating and editing Collections"""
	class Meta:
		model = Collection
		fields = ['title', 'slug', 'is_active', 'order']
		widgets = {
			'title': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'E.g., Summer 2024, Wedding Collection'
			}),
			'slug': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'summer-2024 (lowercase, hyphens only)'
			}),
			'is_active': forms.CheckboxInput(attrs={
				'class': 'form-check-input'
			}),
			'order': forms.NumberInput(attrs={
				'class': 'form-control',
				'placeholder': 'Display order (lower = first)',
				'min': '0'
			}),
		}


class CollectionRowForm(forms.ModelForm):
	"""Form for creating and editing Collection Rows"""
	products = forms.ModelMultipleChoiceField(
		queryset=Product.objects.filter(is_active=True),
		widget=forms.CheckboxSelectMultiple,
		required=False,
		help_text='Select products to display in carousel (shown in order selected)'
	)
	
	class Meta:
		model = CollectionRow
		fields = ['collection', 'title', 'image', 'image_position', 'products', 'order']
		widgets = {
			'collection': forms.Select(attrs={
				'class': 'form-control'
			}),
			'title': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Overlay text on image (optional)'
			}),
			'image': forms.FileInput(attrs={
				'class': 'form-control',
				'accept': 'image/*'
			}),
			'image_position': forms.RadioSelect(attrs={
				'class': 'form-check-input'
			}),
			'order': forms.NumberInput(attrs={
				'class': 'form-control',
				'placeholder': 'Row display order',
				'min': '0'
			}),
		}


class ZoomCarouselItemForm(forms.ModelForm):
	"""Form for creating and editing Zoom Carousel Items"""
	class Meta:
		model = ZoomCarouselItem
		fields = ['title', 'image', 'link_url', 'order', 'is_active']
		widgets = {
			'title': forms.TextInput(attrs={
				'class': 'form-control',
				'placeholder': 'Item title (optional)'
			}),
			'image': forms.FileInput(attrs={
				'class': 'form-control',
				'accept': 'image/*'
			}),
			'link_url': forms.URLInput(attrs={
				'class': 'form-control',
				'placeholder': 'https://example.com/product or collection URL'
			}),
			'order': forms.NumberInput(attrs={
				'class': 'form-control',
				'placeholder': 'Position in carousel',
				'min': '0'
			}),
			'is_active': forms.CheckboxInput(attrs={
				'class': 'form-check-input'
			}),
		}


class ProductSearchForm(forms.Form):
	"""Form for searching and selecting products in admin"""
	search = forms.CharField(
		max_length=200,
		required=False,
		widget=forms.TextInput(attrs={
			'class': 'form-control',
			'placeholder': 'Search by product name or SKU...',
			'id': 'productSearch'
		})
	)
	
	def get_matching_products(self):
		"""Get products matching the search query"""
		search_term = self.cleaned_data.get('search', '')
		query = Product.objects.filter(is_active=True)
		if search_term:
			query = query.filter(name__icontains=search_term)
		return query[:50]  # Limit to first 50 results
