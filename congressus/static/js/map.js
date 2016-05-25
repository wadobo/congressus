(function() {
    var map = window.SeatMap = {};
    map.cbs = $.Callbacks();

    map.showLayout = function(parentObj, obj) {
        var layoutid = obj.data('id');
        var session = obj.data('session');
        var display = '.display-' + session + '-' + layoutid;
        parentObj.find('.display').hide();
        parentObj.find(display).show();
    },

    map.bindLayout = function(obj) {
        obj.find(".seat-L").click(function() {
            var isSelected = $(this).hasClass("seat-selected");
            var seat = $(this);
            if (isSelected) {
                map.cbs.fire("unselect", seat);
                $(this).removeClass("seat-selected");
            } else {
                map.cbs.fire("select", seat);
                $(this).addClass("seat-selected");
            }

        });

        obj.find(".layout").click(function() {
            map.showLayout(obj, $(this));
        });

        obj.find('.display').hide();
    },

    map.showLayoutById = function(parentObj, id) {
        map.showLayout($("#" + id));
    }
}).call(this);
