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

    map.clickSeat = function(obj) {
        var isSelected = obj.hasClass("seat-selected");
        var seat = obj;
        if (isSelected) {
            map.cbs.fire("unselect", seat);
            obj.removeClass("seat-selected");
        } else {
            map.cbs.fire("select", seat);
            obj.addClass("seat-selected");
        }

    },

    map.bindLayout = function(obj) {
        obj.find(".seat-L").unbind("click").click(function() {
            map.clickSeat($(this));
        });

        obj.find(".layout").unbind("click").click(function() {
            map.showLayout(obj, $(this));
        });

        obj.find('.display').hide();
    },

    map.showLayoutById = function(parentObj, id) {
        map.showLayout($("#" + id));
    }
}).call(this);
