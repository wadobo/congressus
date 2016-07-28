function get_initial_data() {
    var deferred = new $.Deferred();
    $.ajax({
        type: "POST",
        data: {},
        dataType: 'JSON',
        url: "/dashboard/general/",
        success: function(msg){
            data_sales_online = msg.sales_online_log;
            data_sales = msg.sales_log;
            data_access = msg.access_log;
            fill_line_charts();
            data_pie_sales_online = msg.sales_pie_online_log;
            data_pie_sales = msg.sales_pie_log;
            data_pie_access = msg.access_pie_log;
            fill_pie_charts();
            deferred.resolve(msg);
        }
    });
    return deferred.promise();
}
get_initial_data();


function fill_line_charts() {
    var ctx_line_sales_online = $("#chart-sales-online").get(0).getContext("2d");
    var ctx_line_sales = $("#chart-sales").get(0).getContext("2d");
    var ctx_line_access = $("#chart-access").get(0).getContext("2d");

    window.chart_line_sales_online = new Chart(ctx_line_sales_online, {
        type: 'line',
        data: data_sales_online,
        options: {
            scales: {yAxes: [{ ticks: { beginAtZero: true }}]}
        }
    });

    window.chart_line_sales = new Chart(ctx_line_sales, {
        type: 'line',
        data: data_sales,
        options: {
            scales: {yAxes: [{ ticks: { beginAtZero: true }}]}
        }
    });

    window.chart_line_access = new Chart(ctx_line_access, {
        type: 'line',
        data: data_access,
        options: {
            scales: {yAxes: [{ ticks: { beginAtZero: true }}]}
        }
    });
}

function fill_pie_charts() {
    var ctx_pie_sales_online = $("#chart-pie-sales-online").get(0).getContext("2d");
    var ctx_pie_sales = $("#chart-pie-sales").get(0).getContext("2d");
    var ctx_pie_access = $("#chart-pie-access").get(0).getContext("2d");

    window.chart_pie_sales_online = new Chart(ctx_pie_sales_online, {
        type: 'doughnut',
        data: data_pie_sales_online,
        options: {
            responsive: true,
        }
    });

    window.chart_pie_sales = new Chart(ctx_pie_sales, {
        type: 'doughnut',
        data: data_pie_sales,
        options: {
            responsive: true,
        }
    });

    window.chart_pie_access = new Chart(ctx_pie_access, {
        type: 'doughnut',
        data: data_pie_access,
        options: {
            responsive: true,
        }
    });
}

function randColor() {
    res = "rgba(";
    res += String(Math.random()*255|0) + ","
    res += String(Math.random()*255|0) + ","
    res += String(Math.random()*255|0) + ","
    res += "1)";
    return res;
}

function update_line_charts(chart, dataset_label, label, amount=1) {
    amount = Number(amount);
    main_dataset = 0
    n = 0
    extra_dataset = null;
    for (var dat in chart.data.datasets) {
        if (chart.data.datasets[dat].label == dataset_label) {
            extra_dataset = n;
            break;
        }
        n++;
    }
    index = chart.data.labels.indexOf(label);
    new_index = false;
    if (index === -1) {
        chart.data.labels.push(label);
        index = chart.data.labels.length - 1;
        new_index = true;
    }

    if (new_index) {
        chart.data.datasets[main_dataset].data.push(amount);
        if (extra_dataset !== null) {
            chart.data.datasets[extra_dataset].data.push(amount);
        }
    } else {
        chart.data.datasets[main_dataset].data[index] += amount;
        if (extra_dataset !== null) {
            chart.data.datasets[extra_dataset].data[index] += amount;
        }
    }
    if (extra_dataset === null) { // Push new dataset
        len_data = chart.data.datasets[main_dataset].data.length;
        new_data = new Array(len_data).fill(0);
        new_data[len_data - 1] = 1;
        chart.data.datasets.push({
            label: dataset_label,
            fill: false,
            lineTension: 0,
            borderColor: randColor(),
            borderWidth: 1,
            pointBorderWidth: 1,
            pointRadius: 1,
            scaleStartValue: 0,
            data: new_data,
        });
    }
    chart.update();
}

function update_pie_charts(chart, label, amount=1) {
    amount = Number(amount);
    index = chart.data.labels.indexOf(label);
    if (index === -1) {
        chart.data.labels.push(label);
        color = randColor();
        chart.data.datasets[0].backgroundColor.push(color);
        chart.data.datasets[0].hoverBackgroundColor.push(color);
        chart.data.datasets[0].data.push(amount);
    } else {
        chart.data.datasets[0].data[index] += amount;
    }
    chart.update();
}

function websocketCB(ev, data) {
    if (ev === 'add_ac') {
        toT = data.date.indexOf('T');
        date = data.date.substring(0, toT);
        update_line_charts(window.chart_line_access, data.control, date);
        update_pie_charts(window.chart_pie_access, data.st);
    } else if (ev === 'add_sale') {
        toT = data.date.indexOf('T');
        date = data.date.substring(0, toT);
        update_line_charts(window.chart_line_sales, data.window, date, data.amount);
        update_pie_charts(window.chart_pie_sales, data.payment);
    }
}

$(document).ready(function() {
    ws.cbs.add(websocketCB);
});
