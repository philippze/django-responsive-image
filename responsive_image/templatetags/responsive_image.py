import math

from easy_thumbnails.files import get_thumbnailer

from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


MIN_SIZE = getattr(settings, 'RESPONSIVE_MIN_SIZE', '360x360')
MAX_SIZE = getattr(settings, 'RESPONSIVE_MAX_SIZE', '2000x2000')


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
        self.factors = self.get_factors()
        self.sizes = self.get_sizes()

    ##

    def get_factors(self):
        min_factor = Size(MIN_SIZE) / self.base_size
        return [min_factor]

    def get_sizes(self):
        sizes = []
        for factor in self.factors:
            sizes.append(
                factor * self.base_size
            )
        return sizes

    # Image operations

    def get_thumbnail(self, size):
        options = {
            'size': list(size),
            'crop': True
        }
        return self.thumbnailer.get_thumbnail(options)

    # Output

    def src(self):
        thumbnail = self.get_thumbnail(self.sizes[0])
        return 'src="%s"' % thumbnail.url


@register.simple_tag
def responsive_image_src(image, ratio):
    img = ResponsiveImage(image, ratio)
    return img.src()

@register.simple_tag
def responsive_image_js():
    return '<script src="%s"></script>' % static(
        'responsive_image/responsive_image.js'
    )
