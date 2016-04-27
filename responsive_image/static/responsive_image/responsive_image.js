(function($) {

    var ResponsiveImage = function(element) {
        this.$image = $(element);
        this.adjust_size();
    };

    ResponsiveImage.prototype = {
        adjust_size: function() {
            //alert('adjust size');
        }
    };

    $.fn.responsiveImage = function() {
        return this.each(function () {
            new ResponsiveImage(this);
        });
    };
}( jQuery ));


jQuery(document).ready(function($) {
    $('img').responsiveImage();
});
