function timerIn(duration, obj, btn) {
    var timer = duration;
    var minutes;
    var seconds;
    var interval = setInterval(function () {
        minutes = parseInt(timer / 60, 10)
        seconds = parseInt(timer % 60, 10);

        minutes = minutes < 10 ? "0" + minutes : minutes;
        seconds = seconds < 10 ? "0" + seconds : seconds;

        obj.text(minutes + ":" + seconds);

        if (--timer < 0) {
            btn.attr('disabled', true);
            clearInterval(interval);
        }
    }, 1000);
}
