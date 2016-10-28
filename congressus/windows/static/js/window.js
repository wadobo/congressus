function ajaxsend() {
    var q = $.post($("form").attr('action'), $("form").serialize(),
        function(response) {
            var pdf = window.open(response);
            setTimeout(function() {
                setTimeout(function() { pdf.close(); }, 1000);
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
    });

    $("input.sessioninput").each(function() {
        if ($(this).attr("type") == 'number') {
            $(this).val("0");
            $(this).change();
        } else {
            $(this).val("0");
        }
    });

    $("[value='']").click();
    $("[value=cash]").click();
    $("#total").val(0);
    $("#change").val(0);
    $("#payed").val("");
    $(".subtotal").each(function() {
        $(this).html(0);
    });
    $("input[autofocus]").trigger('focus');

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
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    sum = apply_discount(sum, ntickets);
    if (sum > 0) {
        $("#finish")[0].disabled = false;
    } else {
        $("#finish")[0].disabled = true;
    }
    $("#total").val(sum);
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
        var msg = $("#finish").data("msg");
        var btn_cancel = $("#finish").data("cancel");
        var btn_ok = $("#finish").data("ok");
        alertify.set({ labels: {
            cancel: btn_cancel,
            ok: btn_ok
        } });
        alertify.confirm(msg, function(e) {
            if (e) {
                args = ' ' + window.windows;
                args += ' ' + moment().format('YYYY-MM-DDThh:mm:ss.SSSSSSZ');
                args += ' ' + $('input[name=payment]:checked').val();
                // BY NUM TICKETS
                //var ntickets = 0;
                //$(".sessioninput").each(function() {
                //    var n = parseInt($(this).val(), 10);
                //    ntickets += n;
                //});
                //args += ' ' + String(ntickets);
                // BY SALE
                args += ' 1'
                ws.send('add_sale' + args);
                setTimeout(clean, 1000);
                ajaxsend();
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
