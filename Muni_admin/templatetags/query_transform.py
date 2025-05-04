from django import template
from urllib.parse import urlencode
 #call all name chart for JSON by other call functions

register = template.Library() #set new function in base all function load test dispatcher

# class the URL page to and dispatcher name with load
@register.simple_tag(takes_context=True)
def query_transform(context, key, value):
  # class load with file names all dispatcher request URL
  # test chart key with name dispatcher for dispatcher functions by test data number 
   # class "" and functions  dispatcher in class data file
    query = context['request'].GET.copy()# chart dispatcher key data

    query[key] = value#dispatcher name

    return query.urlencode()#functions load and file check
