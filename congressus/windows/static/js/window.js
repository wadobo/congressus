var ticket_log = [];
var opened_log = false;
// autocall_singlerow: load in multipurchase.html


function showLog(mode) {
    length = ticket_log.length;
    if (length < 1) {
        return;
    }
    res = '<br/>';
    tail = '<br/>';


    if (mode) {
        ticket_log.forEach(function(tk) {
            name = tk.n + ' - ' + tk.code + ' - ' + tk.mp + ' - ' + tk.price + tail;
            link = "/window/" + window.ev + "/" + window_name + "/" + tk.template + "/" + tk.mp + "/";
            res += "<a href='" + link + "' target='_blank'>" + name + "</a>";
        });
    } else {
        tk = ticket_log[length - 1];
        name = tk.n + ' - ' + tk.code + ' - ' + tk.mp + ' - ' + tk.price + tail;
        link = "/window/" + window.ev + "/" + window_name + "/" + tk.template + "/" + tk.mp + "/";
        res += "<a href='" + link + "' target='_blank'>" + name + "</a>";
    }
    $("#floating-log-input").html(res);
}

function update_ticket_log(mp, code, amount, tpl) {
    if (ticket_log.length >= 10) {
        ticket_log.shift();
    }
    ticket_log.push({mp: mp, template: tpl, code: code, n: amount, price: $("#total").val() + '€'});
    showLog(false);
}

function notifysale(resp, print_format) {
    var mp = resp.mp;
    var wc = resp.wc;
    var nt = resp.nt;
    var tpl = print_format;

    args = ' ' + window.windows;
    args += ' ' + moment().format('YYYY-MM-DDTHH:mm:ss.SSSSSSZ');
    args += ' ' + $('input[name=payment]:checked').val();
    // BY NUM TICKETS
    //args += ' ' + String(nt);
    // BY SALE
    args += ' 1'
    args += ' ' + $("#total").val();
    ws.send('add_sale' + args);

    update_ticket_log(mp, wc, nt, tpl);

    clean();
}

function ajaxsend() {
    var print_format = $('select#print-format')[0].value;
    var q = $.post($("form").attr('action'), $("form").serialize(),
        function(response) {
            notifysale(response, print_format);

            var pdf = window.open(response.url);
            setTimeout(function() {
                if (response.nt < 20 && response.timeout) {
                    setTimeout(function() { pdf.close(); }, response.timeout);
                }
                pdf.print();
            }, 1000);
        });
    q.fail(function(error) {
        alertify.confirm(error.responseJSON.message, function(e) {
            location.reload();
        });
    });
}
window.ajaxsend = ajaxsend;


function clean() {
    $(".seat-selected").each(function() {
        $(this).click();
        $(this).removeClass("seat-selected");
    });
    $("span.label-success").each(function() {
        $(this).text("0");
        $(this).removeClass("label-success");
        $(this).addClass("label-default");
    });

    $("input.sessioninput").each(function() {
        if ($(this).attr("type") == 'number') {
            $(this).val("0");
            $(this).change();
            $(this).keydown(); // keydown to run the seatChange
        } else {
            $(this).val("0");
        }
    });
    $(".seats-input").val("");

    $("[value='']").click();
    $("[value=cash]").click();
    $("#total").val(0);
    $("#change").val(0);
    $("#payed").val("");
    $(".subtotal").each(function() {
        $(this).html(0);
    });
    $("input[autofocus]").trigger('focus');
    cleanSelectedSeat();
    $("#extra-field").val("");

    return false;
}

function calcChange() {
    var total = parseFloat($("#total").val());
    var payed = parseFloat($("#payed").val());
    if (isNaN(payed - total)) {
        $("#change").val(0);
    } else {
        $("#change").val(payed - total);
    }
}

function apply_discount(total, ntickets) {
    var rcheck = $("input[name=discount]:checked");
    var type = rcheck.attr("data-type");
    var value = Number(rcheck.attr("data-value"));
    var unit = rcheck.attr("data-unit") == "True";
    var res = total;
    if (type == 'percent') {
        res = total - total * (value / 100);
    } else if (type == 'amount') {
        if (unit) {
            res -= value * ntickets;
        } else {
            res -= value;
        }
    }
    return res;

}

function recalcTotal() {
    var sum = 0;
    var ntickets = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        ntickets += n;
        var price = parseFloat($(this).data("price").toString().replace(",", "."));
        sum += price * n;
    });
    sum = apply_discount(sum, ntickets);
    $("#total").val(sum);
    if (sum <= 0) {
        $("#finish")[0].disabled = true;
    }
}

$(document).ready(function() {

    // Define tabindex: only for window sale
    if (window.location.pathname.startsWith("/window/")) {
        $("a, summary, select[name=print-format], .minus, .plus, input#clean, input#total, input[name=discount]").attr("tabindex", -1);
        $("details[open] input.sessioninput").each(function(i) {
            $(this).attr('tabindex', i + 1);
        });
        $("label input[name=payment]").attr('tabindex', 0);
        $("input[name=payed]").attr('tabindex', 0);
        $("#finish").attr('tabindex', 0);
    }

    function preConfirmMsg() {
        confirms = preSubmit();
        if (confirms) {
            alertify.confirm(confirms, function(e) {
                if (e) {
                    confirmMsg();
                } else {
                    return false;
                }
            });
        } else {
            confirmMsg();
        }
    }

    function confirmMsg() {
        var ntickets = 0;
        $(".sessioninput").each(function() {
            var n = parseInt($(this).val(), 10);
            ntickets += n;
        });

        var msg = "<b> " + String(ntickets) + "</b> " + $("#finish").data("msg");
        var btn_cancel = $("#finish").data("cancel");
        var btn_ok = $("#finish").data("ok");
        alertify.set({ labels: {
            cancel: btn_cancel,
            ok: btn_ok
        } });
        alertify.confirm(msg, function(e) {
            if (e) {
                ajaxsend();
                if (autocall_singlerow) {
                    singlerow_ajax('request');
                }
            }
        });
    }

    function checkModalOpened() {
        modal_open = false;
        $(".modal").each(function() {
            if (this.style['display'] == 'block') {
                $("#"+this.id+" button.btn")[0].click()
                modal_open = true;
                return false;
            }
        });
        return modal_open;
    }

    $(document).keyup(function(key) {
        // Check ESC key for clean
        if (key.which == 27) {
            if (checkModalOpened()) {
                return;
            }
            if ($("#alertify").length > 0 && ! $("#alertify").hasClass('alertify-hidden')) {
                return;
            }
            clean();
        }
    });

    $(document).keypress(function(key) {
        if (key.which == 13) {
            if (checkModalOpened()) {
                return;
            }
            if ($("#alertify").length > 0 && ! $("#alertify").hasClass('alertify-hidden')) {
                return;
            }
            if ($("#finish")[0].disabled) {
                return;
            }
            preConfirmMsg();
        }
    });

    $("#floating-log").click(function() {
        opened_log = !opened_log;
        showLog(opened_log);
    });

    $("#finish").click(preConfirmMsg);

    $("#clean").click(clean);
    $("#payed").keyup(calcChange);
    $("#payed").click(function() {
        $(this).select();
    });

    $('.sessioninput').change(function() {
        recalcTotal();
    });
    $("input[name=discount]:radio").change(function() {
        recalcTotal();
    });
    recalcTotal();
    calcChange();
});
