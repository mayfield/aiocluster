
$(document).ready(function() {
    (async function() {
        let prof_tpl = $.templates("#prof-template");
        await $.ajax({
            url: '/api/v1/profiler/start',
            method: 'PUT'
        });

        let prev_totals = {};
        let prev_ts = null;
        while (true) {
            let height = 25; // XXX Pull from UI.
            let sortkey = 'inlinetime'; // XXX pull from ui.
            let report = await $.get('/api/v1/profiler/report');
            let ts = (new Date()).getTime();
            let totals = {};
            report.forEach(function(stats) {
                stats.forEach(function(x) {
                    let key = [
                        x.call.file,
                        x.call.function,
                        x.call.lineno
                    ].join(':');
                    if (totals[key] === undefined) {
                        x.stats.call = key;
                        totals[key] = x.stats;
                    } else {
                        let ref = totals[key];
                        ref.totaltime += x['stats']['totaltime'];
                        ref.inlinetime += x['stats']['inlinetime'];
                        ref.callcount += x['stats']['callcount'];
                    }
                });
            });
            if (prev_ts === null) {
                prev_ts = ts;
                prev_totals = totals;
                console.log("<b>Collecting...</b>"); // XXX report to UI
                await sleep(0.100);  // Short loop initial to get something up.
                continue;
            }
            let period = (ts - prev_ts) / 1000;
            Object.keys(totals).forEach(function(call) {
                let stats = totals[call];
                if (prev_totals[call] !== undefined) {
                    let prev = prev_totals[call];
                    let sample_total = stats.inlinetime - prev.inlinetime;
                    sample_calls = stats.callcount - prev.callcount;
                    stats.cpu_percent = sample_total / period;
                    stats.call_rate = sample_calls / period;
                    if (sample_calls !== 0)
                        stats.percall_time = sample_total / sample_calls;
                    else
                        stats.percall_time = 0;
                } else {
                    stats.cpu_percent = 0;
                    stats.call_rate = 0;
                    stats.percall_time = 0;
                }
            });
            prev_ts = ts;
            prev_totals = totals;
            let stats = Object.keys(totals).map(key => totals[key]);
            //let newstats = stats.sort((a, b) => a < b ? 1 : -1);
            let newstats = stats.sort((a, b) => a[sortkey] < b[sortkey] ? 1 : -1);
            $('#prof-holder').html(prof_tpl.render({stats: newstats}));
            await sleep(1);
        }
    })();
});
