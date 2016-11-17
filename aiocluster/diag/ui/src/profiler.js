"use strict";

$(document).ready(function() {
    (async function() {
        const tpl_tag = $('#prof-template');
        const tpl = Handlebars.compile(tpl_tag.html());
        const target_el = tpl_tag.parent();

        await aioc.api.put('profiler/active', true);

        let prev_totals = {};
        let prev_ts = null;
        while (true) {
            let height = 25; // XXX Pull from UI.
            let sortkey = 'inlinetime'; // XXX pull from ui.
            let report = await aioc.api.get('profiler/report');
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
                await aioc.util.sleep(0.100);  // Short loop initial to get something up.
                continue;
            }
            let period = (ts - prev_ts) / 1000;
            Object.keys(totals).forEach(function(call) {
                let stats = totals[call];
                if (prev_totals[call] !== undefined) {
                    const prev = prev_totals[call];
                    const sample_total = stats.inlinetime - prev.inlinetime;
                    const sample_calls = stats.callcount - prev.callcount;
                    stats.cpu_percent = sample_total / period;
                    stats.call_rate = sample_calls / period;
                    if (sample_calls !== 0)
                        stats.percall_time = (sample_total / sample_calls) * 1000000;
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
            let newstats = stats.sort((a, b) => a[sortkey] < b[sortkey] ? 1 : -1);
            $('#prof-holder').html(tpl({stats: newstats}));
            await aioc.util.sleep(1); /* XXX pull from UI */
        }
    })();
});
