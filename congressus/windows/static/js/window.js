var ticket_log = [];
var opened_log = false;
// autocall_singlerow: load in multipurchase.html


function get_template_id(tk) {
  var tpl_id = 1;
  var tpl = tk.session.template;
  if (tpl) {
      tpl_id = tpl.id;
  }
  return tpl_id;
}

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
            link = "/window/" + window.ev + "/" + window_name + "/" + get_template_id(tk) + "/" + tk.mp + "/";
            res += "<a href='" + link + "' target='_blank'>" + name + "</a>";
        });
    } else {
        tk = ticket_log[length - 1];
        name = tk.n + ' - ' + tk.code + ' - ' + tk.mp + ' - ' + tk.price + tail;
        link = "/window/" + window.ev + "/" + window_name + "/" + get_template_id(tk) + "/" + tk.mp + "/";
        res += "<a href='" + link + "' target='_blank'>" + name + "</a>";
    }
    $("#floating-log-input").html(res);
}

function update_ticket_log(mp, code, amount) {
    if (ticket_log.length >= 10) {
        ticket_log.shift();
    }
    ticket_log.push({mp: mp, code: code, n: amount, price: $("#total").val() + '€'});
    showLog(false);
}

function notifysale(resp) {
    var mp = resp.mp;
    var wc = resp.wc;
    var nt = resp.nt;

    args = ' ' + window.windows;
    args += ' ' + moment().format('YYYY-MM-DDTHH:mm:ss.SSSSSSZ');
    args += ' ' + $('input[name=payment]:checked').val();
    // BY NUM TICKETS
    //args += ' ' + String(nt);
    // BY SALE
    args += ' 1'
    args += ' ' + $("#total").val();
    ws.send('add_sale' + args);

    update_ticket_log(mp, wc, nt);

    clean();
}

function ajaxsend() {
    var q = $.post($("form").attr('action'), $("form").serialize(),
        function(response) {
            notifysale(response);

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
        var price = parseFloat($(this).data("price").replace(",", "."));
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
        $('.sessioninput').each(function(i) {
            $(this).attr('tabindex', i + 1);
        });
        index = $('.sessioninput').length + 1;
        //$("input[name=discount]").attr('tabindex', index++);
        $("input[name=payment]").attr('tabindex', index++);
        $("input[name=payed]").attr('tabindex', index++);
        $("#finish").attr('tabindex', index++);
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
