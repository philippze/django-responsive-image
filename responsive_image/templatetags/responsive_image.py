import math

from classytags.arguments import Argument, Flag
from classytags.core import Options
from easy_thumbnails.files import get_thumbnailer
from sekizai.helpers import get_varname
from sekizai.templatetags.sekizai_tags import SekizaiTag, SekizaiParser

from django import template
from django.conf import settings
from django.template import Context, Template
from django.templatetags.static import static

register = template.Library()


MIN_SIZE = getattr(settings, 'RESPONSIVE_MIN_SIZE', '360x360')
MAX_SIZE = getattr(settings, 'RESPONSIVE_MAX_SIZE', '2000x2000')

HTML = """
    <div class="responsive-image">
        <img src="{{ src }}" />
        <div class="responsive-image__background responsive-image__background-{{ count }}"></div>
    </div>
"""

STYLE = """
@media(min-width: {{ width }}px) {
    .responsive-image__background-{{ count }} {
        background-image: url('{{ url }}');
    }
}
"""

GLOBAL_STYLE = """
.responsive-image {
    position: relative;
}
.responsive-image img {
    width: 100%;
}
.responsive-image__background {
    background-size: 100% 100%;
    bottom: 0;
    position: absolute;
    left: 0;
    right: 0;
    top: 0;
}
"""

class ResponsiveImageException(Exception):
    pass

class MyException(Exception):
    pass


class Size(object):
    def __init__(self, value):
        try:
            self.init_with_string(value)
        except MyException:
            try:
                self.init_with_tuple(value)
            except MyException:
                self.raise_init_exception(value)

    def init_with_string(self, value):
        try:
            x, y = value.split('x')
        except AttributeError:
            raise MyException
        self.set_integer_tuple(x, y)

    def init_with_tuple(self, value):
        try:
            x, y = value
        except TypeError:
            raise MyException
        self.set_integer_tuple(x, y)

    def set_integer_tuple(self, x, y):
        self.x, self.y = self.integer_tuple(x, y)

    def integer_tuple(self, x, y):
        try:
            return (int(x), int(y))
        except ValueError:
            raise MyException

    def raise_init_exception(self, value):
        raise ResponsiveImageException(
            'Size initialized with inappropriate argument '
            + str(value)
            + '. Should be <width>x<height> or tuple of numbers.'
        )

    def __str__(self):
        return '%dx%d' % list(self)

    def __iter__(self):
        return (self.x, self.y).__iter__()

    def __truediv__(self, other):
        """Return the ceil of the higher divisor"""
        divisor_x = self.x / other.x
        divisor_y = self.y / other.y
        divisor = max(divisor_x, divisor_y)
        return math.ceil(divisor)

    def __mul__(self, factor):
        """Scalar multiplication"""
        new_x = factor * self.x
        new_y = factor * self.y
        return Size((new_x, new_y))

    __rmul__ = __mul__


class ResponsiveImage(object):

    def __init__(self, image, ratio):
        self.thumbnailer = get_thumbnailer(image)
        self.base_size = Size(ratio)

    # Image operations

    def get_thumbnail(self, size):
        options = {
            'size': list(size),
            'crop': True
        }
        return self.thumbnailer.get_thumbnail(options)

    def for_width(self, width):
        factor = width / self.base_size.x
        if width % self.base_size.x > 0:
            factor += 1
        options = {
            'size': list(factor * self.base_size),
            'crop': True
        }
        return self.thumbnailer.get_thumbnail(options)

    # Output

    def src(self):
        thumbnail = self.get_thumbnail(self.base_size)
        return thumbnail.url


@register.simple_tag
def responsive_image_src(image, ratio):
    img = ResponsiveImage(image, ratio)
    return img.src()

@register.simple_tag
def responsive_image_js():
    return '<script src="%s"></script>' % static(
        'responsive_image/responsive_image.js'
    )

class ResponsiveImageTag(SekizaiTag):
    name = 'responsive_image'

    options = Options(
        Argument('image'),
        Argument('ratio'),
        parser_class=SekizaiParser,
    )

    def render_tag(self, context, image, ratio, nodelist):
        self.image = ResponsiveImage(image, ratio)
        varname = get_varname()
        count = context[varname].get('responsive-img-count', '1')
        try:
            count = int(count)
        except TypeError:
            count = 1
        self.remember(context, count)
        return self.html(image, ratio, count)

    def remember(self, context, count):
        #print (count)
        #print (count.__class__)
        name = 'css'
        varname = get_varname()
        context[varname]['responsive-img-count'] = '%s' % (count + 1)
        style_tag = self.style(300, count)
        context[varname][name].append(style_tag)
        if count == '1':
            context[varname][name].append('<style>%s</style>' % GLOBAL_STYLE)

    def html(self, image, ratio, count):
        src = self.image.src()
        template = Template(HTML)
        context = Context({'src': src, 'count': count})
        return template.render(context)

    def style(self, width, count):
        thumbnail = self.image.for_width(width)
        url = thumbnail.url
        style = Template(STYLE)
        context = Context({'width': 300, 'count': count, 'url': url})
        return '<style>%s</style>' % style.render(context)

register.tag('responsive_image', ResponsiveImageTag)
