from django.shortcuts import render
from django.db.models import Q
from .models import CorporateFiling
from datetime import datetime

def index(request):
    # Get all filings ordered by filing date
    filings = CorporateFiling.objects.all().order_by('-filing_date')
    
    # Get search parameters
    company_name = request.GET.get('company_name', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    category = request.GET.get('category', '')
    
    # Apply filters if provided
    if company_name:
        filings = filings.filter(company_name__icontains=company_name)
    
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            filings = filings.filter(filing_date__gte=start_date)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            filings = filings.filter(filing_date__lte=end_date)
        except ValueError:
            pass
    
    if category:
        filings = filings.filter(category=category)
    
    # Get distinct categories for dropdown
    category_values = CorporateFiling.objects.values_list('category', flat=True)
    # Use a set to ensure uniqueness, filter None values, and convert back to sorted list
    categories = sorted(set(c for c in category_values if c))
    
    context = {
        'filings': filings,
        'company_name': company_name,
        'start_date': start_date,
        'end_date': end_date,
        'selected_category': category,
        'categories': categories,
    }
    
    return render(request, 'app/index.html', context)
