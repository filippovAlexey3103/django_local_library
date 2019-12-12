from django.shortcuts import render, get_object_or_404
from django.views import generic
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import permission_required
from django.contrib import messages

from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
import datetime

from .models import Book, Author, BookInstance, Genre
from .forms import RenewBookForm, RenewBookModelForm

# Create your views here.
def index(request):
    """
    Функция отображения для домашней страницы сайта.
    """
    # Генерация "количеств" некоторых главных объектов
    num_books=Book.objects.all().count()
    num_instances=BookInstance.objects.all().count()
    # Доступные книги (статус = 'a')
    num_instances_available=BookInstance.objects.filter(status__exact='a').count()
    num_authors=Author.objects.count()  # Метод 'all()' применен по умолчанию.

    num_books_filter=Book.objects.filter(title__contains='Гарри').count()
    num_genres_filter=Genre.objects.filter(name__contains='Роман').count()

    # Number of visits to this view, as counted in the session variable.
    num_visits=request.session.get('num_visits', 0)
    request.session['num_visits'] = num_visits+1
    
    # Отрисовка HTML-шаблона index.html с данными внутри 
    # переменной контекста context
    return render(
        request,
        'index.html',
        context={
        	'num_books':num_books,
        	'num_instances':num_instances,
        	'num_instances_available':num_instances_available,
        	'num_authors':num_authors,
        	'num_books_filter':num_books_filter,
        	'num_genres_filter':num_genres_filter,
        	'num_visits':num_visits,
        },
    )

class BookListView(generic.ListView):
    model = Book
    # context_object_name = 'my_book_list'   # ваше собственное имя переменной контекста в шаблоне
    # queryset = Book.objects.filter(title__icontains='war')[:5] # Получение 5 книг, содержащих слово 'war' в заголовке
    # template_name = 'books/my_arbitrary_template_name_list.html'  # Определение имени вашего шаблона и его расположения
    paginate_by = 10

class BookDetailView(generic.DetailView):
    model = Book

class AuthorListView(generic.ListView):
    model = Author
    paginate_by = 10

class AuthorDetailView(generic.DetailView):
    model = Author

class LoanedBooksByUserListView(LoginRequiredMixin,generic.ListView):
    """
    Generic class-based view listing books on loan to current user. 
    """
    model = BookInstance
    template_name ='catalog/bookinstance_list_borrowed_user.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(borrower=self.request.user).filter(status__exact='o').order_by('due_back')

class AllLoanedBooksListView(LoginRequiredMixin, PermissionRequiredMixin, generic.ListView):
    """
    Generic class-based view listing books on loan to user library staff. 
    """
    permission_required = 'catalog.can_mark_returned'
    model = BookInstance
    template_name ='catalog/bookinstance_list_all_borrowed.html'
    paginate_by = 10
    
    def get_queryset(self):
        return BookInstance.objects.filter(status__exact='o').order_by('due_back')

# view for update due_back field in BookInstance
@permission_required('catalog.can_mark_returned')
def renew_book_librarian(request, pk):
    """
    View function for renewing a specific BookInstance by librarian
    """
    book_inst=get_object_or_404(BookInstance, pk = pk)

    # If this is a POST request then process the Form data
    if request.method == 'POST':

        # Create a form instance and populate it with data from the request (binding):
        form = RenewBookForm(request.POST)

        # Check if the form is valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required (here we just write it to the model due_back field)
            book_inst.due_back = form.cleaned_data['renewal_date']
            book_inst.save()

            # redirect to a new URL:
            return HttpResponseRedirect(reverse('all-borrowed') )

    # If this is a GET (or any other method) create the default form.
    else:
        proposed_renewal_date = datetime.date.today() + datetime.timedelta(weeks=3)
        form = RenewBookForm(initial={'renewal_date': proposed_renewal_date,})

    return render(request, 'catalog/book_renew_librarian.html', {'form': form, 'bookinst':book_inst})


class AuthorCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'catalog.add_author'

    model = Author
    fields = '__all__'
    initial={'date_of_death':datetime.datetime.strptime('12/10/2016', '%d/%m/%Y'),}

class AuthorUpdate(PermissionRequiredMixin, generic.edit.UpdateView):
    permission_required = 'catalog.change_author'

    model = Author
    fields = ['first_name','last_name','date_of_birth','date_of_death']

class AuthorDelete(PermissionRequiredMixin, generic.edit.DeleteView):
    permission_required = 'catalog.delete_author'

    model = Author
    success_url = reverse_lazy('authors')

class BookCreate(PermissionRequiredMixin, generic.edit.CreateView):
    permission_required = 'catalog.add_book'

    model = Book
    fields = '__all__'
    # initial={,}

class BookUpdate(PermissionRequiredMixin, generic.edit.UpdateView):
    permission_required = 'catalog.change_book'

    model = Book
    fields = '__all__'

class BookDelete(PermissionRequiredMixin, generic.edit.DeleteView):
    permission_required = 'catalog.delete_book'

    model = Book
    success_url = reverse_lazy('books')