(function() {
    var ws = window.ws = {};
    ws.socket = null;
    ws.cbs = $.Callbacks();

    ws.init = function(server) {
        ws.socket = new WebSocket("ws://"+server, 'congressus');
        ws.socket.onmessage = function(ev) {
            var data = JSON.parse(ev.data);
            if (data.action) {
                ws.cbs.fire(data.action, data);
            } else {
                ws.cbs.fire('msg', ev);
            }
        };
        ws.socket.onopen = function (ev) { ws.cbs.fire('open', ev); };
        ws.socket.onclose = function (ev) { ws.cbs.fire('close', ev); };
        ws.socket.onerror = function (ev) { ws.cbs.fire('error', ev); };
    };

    ws.send = function(msg) {
        ws.socket.send(msg);
    };
}).call(this);
