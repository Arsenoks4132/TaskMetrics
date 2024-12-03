from django import template

register = template.Library()


@register.inclusion_tag('form.html')
def post_form(form=None, button='Отправить'):
    return {'form': form, 'button': button}
