function get_initial_data() {
    var ev = window.ev;
    var dash = window.dash;
    var deferred = new $.Deferred();
    $.ajax({
        type: "POST",
        data: {},
        dataType: 'JSON',
        url: "/dashboard/"+ev+"/"+dash+"/",
        success: function(msg){
            charts = msg.charts;
            fill_charts();
            deferred.resolve(msg);
        }
    });
    return deferred.promise();
}
get_initial_data();


function fill_charts() {
    window.data_charts = {'ws': [], 'os': [], 'a': []};
    for (c=0; c < charts.length; c++) {
        type_chart = charts[c].type_chart;
        type_data = charts[c].type_data;
        id = type_data + String(c);
        var canvas = $('<canvas id="'+id+'" width="400" height="200"></canvas>');
        //var html = '<div class="row">';
        //html += '<div class="col-md-12">';
        //html += canvas;
        //html += '</div>';
        //html += '</div>';

        //console.log(charts);
        var title = charts[c].title;
        var container = $('<div class="col-sm-'+num_cols+'"></div>');
        var panel = $('<div class="panel panel-default"></div>');
        var head = $('<div class="panel-heading">'+ title +'</div>');
        var body = $('<div class="panel-body"></div>');

        body.append(canvas);
        panel.append(head);
        panel.append(body);
        container.append(panel)

        $("#charts").append(container);
        var ctx = canvas.get(0).getContext("2d");
        if (type_chart == 'p') {
            type = 'doughnut';
            options = {responsive: true};
        } else if (type_chart == 'c') {
            type = 'line';
            options = {yAxes: [{ ticks: { beginAtZero: true }}]};
        } else if (type_chart == 'b') {
            type = 'bar';
            options = {yAxes: [{ ticks: { beginAtZero: true }}]};
        }
        window.data_charts[type_data].push(new Chart(ctx, {
            type: type,
            data: charts[c].data,
            options: options
        }));
    }
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

function update_bar_charts(chart, dataset_label, label, price) {
    price = Number(price);
    index = chart.data.labels.indexOf(dataset_label);
    chart.data.datasets[0].data[index] += price;
    chart.update();
}

function get_date(date, ex_label) {
    // get date with the correct format for the graphic labels
    toT = date.indexOf('T');
    res = date.substring(0, toT);

    // Search label example and check if interval is daily, hourly o each minute
    index = ex_label.indexOf(' ');
    if (index == 3) { // hourly
        res = date.substring(toT+1, toT+index) + 'h ' + res;
    } else if (index == 5) { // each minute
        res = date.substring(toT+1, toT+1+index) + ' ' + res;
    }
    return res;
}

function websocketCB(ev, data) {
    if (ev === 'add_ac') {
        for (c=0; c < window.data_charts['a'].length; c++) {
            d = window.data_charts['a'][c];
            if (d.config.type == 'doughnut') {
                update_pie_charts(d, data.st);
            } else if (d.config.type == 'line') {
                date = get_date(data.date, d.config.data.labels[0]);
                update_line_charts(d, data.control, date);
            }
        }
    } else if (ev === 'add_online_sale') {
        for (c=0; c < window.data_charts['os'].length; c++) {
            d = window.data_charts['os'][c];
            if (d.config.type == 'doughnut') {
                update_pie_charts(d, data.payment);
            } else if (d.config.type == 'line') {
                date = get_date(data.date, d.config.data.labels[0]);
                update_line_charts(d, data.window, date, data.amount);
            }
        }
    } else if (ev === 'add_sale') {
        for (c=0; c < window.data_charts['ws'].length; c++) {
            d = window.data_charts['ws'][c];
            if (d.config.type == 'doughnut') {
                update_pie_charts(d, data.payment);
            } else if (d.config.type == 'line') {
                date = get_date(data.date, d.config.data.labels[0]);
                update_line_charts(d, data.window, date, data.amount);
            } else if (d.config.type == 'bar') {
                date = get_date(data.date, d.config.data.labels[0]);
                update_bar_charts(d, data.window, date, data.price);
            }
        }
    }
}

$(document).ready(function() {
    ws.cbs.add(websocketCB);
});
