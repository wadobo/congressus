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

    $("[value=none]").click();
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

function reload() {
    location.reload();
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

function apply_discount(total) {
    var rcheck = $("input[name=discount]:checked");
    var type = rcheck.attr("data-type");
    var value = (rcheck.attr("data-value"));
    if (type == 'none') {
        res = total;
    } else if (type == 'percent') {
        res = total - total * (value / 100);
    } else if (type == 'amount') {
        res -= value;
    } else {
        res = total;
    }
    return res;

}

function recalcTotal() {
    var sum = 0;
    $(".sessioninput").each(function() {
        var n = parseInt($(this).val(), 10);
        var price = parseFloat($(this).data("price"));
        sum += price * n;
    });
    sum = apply_discount(sum);
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
                args += ' ' + $(".seat-selected").length;
                ws.send('add_sale' + args);
                setTimeout(reload, 1000);
                $("form").submit();
            }
        });
    }

    $(document).keypress(function(key) {
        if (key.which == 13) {
            if ($("#alertify").length > 0 && ! $("#alertify").hasClass('alertify-hidden')) {
                return;
            }
            if ($("#finish")[0].disabled) {
                return;
            }
            confirmMsg();
        }
    });

    $("#finish").click(confirmMsg);

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
