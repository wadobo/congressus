(function() {
    var map = window.SeatMap = {};
    map.cbs = $.Callbacks();

    map.showLayout = function(parentObj, obj) {
        var layoutid = obj.data('id');
        var session = obj.data('session');
        var display = '.display-' + session + '-' + layoutid;
        parentObj.find('.display').hide();
        parentObj.find(display).show();
        try { parentObj.find("#separator")[0].scrollIntoView(true); } catch (e) {};
    },

    map.clickSeat = function(obj) {
        var isSelected = obj.hasClass("seat-selected");
        var seat = obj;
        if (isSelected) {
            map.cbs.fire("unselect", seat);
            obj.removeClass("seat-selected");
        } else {
            id = seat.data("session");
            selected_seat = $('#'+id).val();
            if (selected_seat >= Number(window.MAX_SEAT_BY_SESSION)) {
                alertify.alert("No se pueden seleccionar más de " + window.MAX_SEAT_BY_SESSION + " asientos.")
            } else {
                map.cbs.fire("select", seat);
                obj.addClass("seat-selected");
            }
        }

    },

    map.preloadLayout = function(layout, obj, f) {
        var url = obj.data('url');

        if (!obj.find(".ajax-loading").length) {
            f();
            return;
        }

        var get = $.get(url, function(data) {
            obj.append(data);
            obj.find(".ajax-loading").remove();
            // binding click
            obj.find(".seat-L").unbind("click").click(function() {
                map.clickSeat($(this));
            });
            // binding show for the next click
            layout.unbind("click").click(function() {
                map.showLayout(obj.parent(), layout);
            });

            f();
        });
    },

    map.loadLayout = function(parentObj, obj) {
        var session = obj.data('session');
        var layout = obj.data('id');

        var display = '.display-' + session + '-' + layout;
        parentObj.find('.display').hide();
        parentObj.find(display).show();

        var obj1 = $(display);
        var url = obj1.data('url');
        var get = $.get(url, function(data) {
            obj1.append(data);
            obj1.find(".ajax-loading").remove();
            map.showLayout(parentObj, obj);

            // binding click
            parentObj.find(".seat-L").unbind("click").click(function() {
                map.clickSeat($(this));
            });

        });

        // binding show for the next click
        obj.unbind("click").click(function() {
            map.showLayout(parentObj, obj);
        });
    },

    map.bindLayout = function(obj) {
        obj.find(".layout").unbind("click").click(function() {
            map.loadLayout(obj, $(this));
            try { $("#separator")[0].scrollIntoView(true); } catch (e) {};
        });

        obj.find('.display').hide();
    },

    map.showLayoutById = function(parentObj, id) {
        map.showLayout($("#" + id));
    }
}).call(this);
