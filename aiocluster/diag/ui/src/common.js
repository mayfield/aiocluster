
function megabytes(val) {
    return Math.round(val / 1024 / 1024).toString() + ' MB';
}
$.views.converters("megabytes", megabytes);


function percent(val) {
    return Math.round(val * 100).toString() + '%';
}
$.views.converters("percent", percent);


function humantime(val) {
    return moment.duration(val, 'seconds').humanize();
}
$.views.converters("humantime", humantime);


function humanint(val) {
    let units = [
        [1000000000000, 't'],
        [1000000000, 'b'],
        [1000000, 'm'],
        [1000, 'k'],
        [0, ''],
    ];
    let prec = 1;
    for (let i=0; i < units.length; i++) {
        let unit = units[i];
        if (Math.abs(val) >= unit[0]) {
            if (unit[0] !== 0)
                val /= unit[0];
            let s = val.toFixed(prec).replace(/0+$/, '') + unit[1];
            return s.replace(/\.$/, '');
        } 
    }
}
$.views.converters("humanint", humanint);

$.views.converters("round", Math.round);


async function sleep(seconds) {
    await new Promise(r => setTimeout(r, seconds * 1000));
}
